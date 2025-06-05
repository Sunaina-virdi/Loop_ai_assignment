from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from enum import Enum
import uuid
import asyncio
from collections import deque
from typing import List, Dict
from datetime import datetime

app = FastAPI()

class PriorityEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IngestRequest(BaseModel):
    ids: List[int]
    priority: PriorityEnum

class Batch:
    def __init__(self, ids, priority, ingestion_id):
        self.batch_id = str(uuid.uuid4())
        self.ids = ids
        self.priority = priority
        self.status = "yet_to_start"
        self.ingestion_id = ingestion_id
        self.created_time = datetime.utcnow()

# In-memory stores
ingestions: Dict[str, Dict] = {}
batch_queue = deque()
processing_lock = asyncio.Lock()

# Priority map
priority_value = {
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3
}

@app.post("/ingest")
async def ingest_data(request: IngestRequest, background_tasks: BackgroundTasks):
    ingestion_id = str(uuid.uuid4())
    ids = request.ids
    priority = request.priority

    # Split ids into batches of 3
    batches = [Batch(ids[i:i+3], priority, ingestion_id) for i in range(0, len(ids), 3)]
    
    # Save ingestion record
    ingestions[ingestion_id] = {
        "ingestion_id": ingestion_id,
        "status": "yet_to_start",
        "batches": batches
    }

    # Enqueue batches
    for batch in batches:
        batch_queue.append((priority_value[priority], batch.created_time, batch))

    # Sort queue by priority and creation time
    batch_queue_sorted = sorted(list(batch_queue), key=lambda x: (x[0], x[1]))
    batch_queue.clear()
    batch_queue.extend(batch_queue_sorted)

    # Start background processing
    background_tasks.add_task(process_batches)

    return {"ingestion_id": ingestion_id}

@app.get("/status/{ingestion_id}")
async def get_status(ingestion_id: str):
    if ingestion_id not in ingestions:
        raise HTTPException(status_code=404, detail="Ingestion ID not found")

    ingestion = ingestions[ingestion_id]
    batch_statuses = [batch.status for batch in ingestion["batches"]]

    if all(status == "yet_to_start" for status in batch_statuses):
        ingestion["status"] = "yet_to_start"
    elif all(status == "completed" for status in batch_statuses):
        ingestion["status"] = "completed"
    else:
        ingestion["status"] = "triggered"

    return {
        "ingestion_id": ingestion_id,
        "status": ingestion["status"],
        "batches": [
            {"batch_id": batch.batch_id, "ids": batch.ids, "status": batch.status}
            for batch in ingestion["batches"]
        ]
    }

async def simulate_external_call(id):
    await asyncio.sleep(1)  # simulate delay
    return {"id": id, "data": "processed"}

async def process_batches():
    async with processing_lock:
        while batch_queue:
            _, _, batch = batch_queue.popleft()
            batch.status = "triggered"

            tasks = [simulate_external_call(id) for id in batch.ids]
            await asyncio.gather(*tasks)

            batch.status = "completed"
            await asyncio.sleep(5)  # rate limit

# For running locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
