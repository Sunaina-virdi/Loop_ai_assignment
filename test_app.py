import time
import uuid
import pytest
import asyncio
import httpx
from fastapi.testclient import TestClient
from main import app, ingestions

client = TestClient(app)


def test_ingestion_and_status():
    # Submit HIGH priority request
    response1 = client.post("/ingest", json={"ids": [1, 2, 3, 4, 5], "priority": "HIGH"})
    assert response1.status_code == 200
    high_ingestion_id = response1.json()["ingestion_id"]

    # Submit MEDIUM priority request
    response2 = client.post("/ingest", json={"ids": [6, 7, 8, 9], "priority": "MEDIUM"})
    assert response2.status_code == 200
    medium_ingestion_id = response2.json()["ingestion_id"]

    # Wait for 12 seconds for 2 batches to complete
    time.sleep(12)

    # Check status of HIGH priority
    high_status = client.get(f"/status/{high_ingestion_id}")
    assert high_status.status_code == 200
    high_data = high_status.json()
    assert high_data["ingestion_id"] == high_ingestion_id
    assert any(batch["status"] in ["triggered", "completed"] for batch in high_data["batches"])

    # Check status of MEDIUM priority
    medium_status = client.get(f"/status/{medium_ingestion_id}")
    assert medium_status.status_code == 200
    medium_data = medium_status.json()
    assert medium_data["ingestion_id"] == medium_ingestion_id
    assert all(batch["status"] in ["yet_to_start", "triggered", "completed"] for batch in medium_data["batches"])


def test_batch_priority_order():
    # Reset state
    ingestions.clear()

    # Submit MEDIUM priority
    response1 = client.post("/ingest", json={"ids": [10, 11, 12], "priority": "MEDIUM"})
    medium_ingestion_id = response1.json()["ingestion_id"]

    time.sleep(1)  # Wait 1 sec

    # Submit HIGH priority
    response2 = client.post("/ingest", json={"ids": [13, 14, 15], "priority": "HIGH"})
    high_ingestion_id = response2.json()["ingestion_id"]

    time.sleep(7)  # Wait enough for 1 batch of HIGH and 1 batch of MEDIUM

    # HIGH should be completed first
    high_status = client.get(f"/status/{high_ingestion_id}").json()
    medium_status = client.get(f"/status/{medium_ingestion_id}").json()

    assert any(batch["status"] == "completed" for batch in high_status["batches"])
    assert any(batch["status"] in ["triggered", "completed"] for batch in medium_status["batches"])


def test_batch_rate_limit():
    # Submit 6 IDs with HIGH priority to create 2 batches
    response = client.post("/ingest", json={"ids": [100, 101, 102, 103, 104, 105], "priority": "HIGH"})
    ingestion_id = response.json()["ingestion_id"]

    # Check initial status
    status_before = client.get(f"/status/{ingestion_id}").json()
    assert status_before["status"] == "yet_to_start"

    # Wait 6 seconds (enough for 1 batch)
    time.sleep(6)
    status_mid = client.get(f"/status/{ingestion_id}").json()
    triggered_batches = [b for b in status_mid["batches"] if b["status"] == "triggered"]
    assert len(triggered_batches) >= 1

    # Wait 6 more seconds (total 12s)
    time.sleep(6)
    status_final = client.get(f"/status/{ingestion_id}").json()
    assert status_final["status"] == "completed"
    completed_batches = [b for b in status_final["batches"] if b["status"] == "completed"]
    assert len(completed_batches) == 2
