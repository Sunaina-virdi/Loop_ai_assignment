# Data Ingestion API System

## 📌 Overview

This project is a RESTful API service that allows clients to submit data ingestion requests. The requests are:

* Processed in **batches of up to 3 IDs**
* Rate-limited to **1 batch every 5 seconds**
* Executed **asynchronously** with priority handling (**HIGH > MEDIUM > LOW**)

## 🚀 Features

* `/ingest`: Submit ingestion jobs with priority
* `/status/<ingestion_id>`: Track status of ingestion jobs and their batches
* Prioritized and timed batch execution
* Background processing using FastAPI background tasks

## 🛠 Tech Stack

* Python 3.10+
* FastAPI
* Uvicorn
* pytest (for testing)

## 📦 Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd your-repo-folder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

### 🧪 Run the app

```bash
uvicorn main:app --reload
```

### ✅ Run Tests

```bash
pytest test_app.py
```

---

## 📬 API Usage

### 1. `POST /ingest`

Submit a new ingestion request.

#### Request

```json
{
  "ids": [1, 2, 3, 4, 5],
  "priority": "HIGH"
}
```

#### Response

```json
{
  "ingestion_id": "abc123"
}
```

---

### 2. `GET /status/<ingestion_id>`

Get the status of ingestion and its batches.

#### Response

```json
{
  "ingestion_id": "abc123",
  "status": "triggered",
  "batches": [
    {"batch_id": "uuid1", "ids": [1, 2, 3], "status": "completed"},
    {"batch_id": "uuid2", "ids": [4, 5], "status": "triggered"}
  ]
}
```

## 🧠 Status Definitions

**Ingestion Status**:

* `yet_to_start`: All batches are pending
* `triggered`: At least one batch started
* `completed`: All batches completed

**Batch Status**:

* `yet_to_start`
* `triggered`
* `completed`

## 📂 Folder Structure

```
.
├── main.py          # FastAPI app logic
├── test_app.py      # Test suite using pytest
├── README.md        # This file
├── requirements.txt # Python dependencies
```

## 📝 Sample curl Commands

```bash
# Ingest request
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"ids": [1,2,3,4,5], "priority": "HIGH"}'

# Get status
curl http://localhost:8000/status/<ingestion_id>
```

---
