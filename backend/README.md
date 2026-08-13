# HITRAG Backend Service

FastAPI backend for **HITRAG** — the institutional Retrieval-Augmented Generation (RAG) system for Harare Institute of Technology (HIT).

## Phase 1 Service Skeleton

This phase scaffolds the core application layout and provides a working `/health` diagnostic endpoint.

## Local Setup Instructions

### 1. Create a Python Virtual Environment
Navigate to the `backend/` directory:
```bash
cd backend
python3 -m venv .venv
```

### 2. Activate the Virtual Environment
- **macOS/Linux**:
  ```bash
  source .venv/bin/activate
  ```
- **Windows**:
  ```cmd
  .venv\Scripts\activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the API Server
Start the Uvicorn development server with hot-reload enabled:
```bash
uvicorn app.main:app --reload
```

### 5. Verify the `/health` Endpoint
Open your browser or run via `curl`:
```bash
curl http://127.0.0.1:8000/health
```

Expected Response:
```json
{"status":"ok"}
```

### 6. Run Automated Tests
```bash
pytest
```
