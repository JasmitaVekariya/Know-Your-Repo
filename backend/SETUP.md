# Quick Setup Guide

## Prerequisites
- Python 3.9+ (3.11 recommended)
- pip

## Installation Steps

1. **Create virtual environment** (recommended):
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Create .env file** (optional for Phase 2):
```bash
# Create .env file with:
GEMINI_API_KEY=
MONGO_URI=
```

4. **Run the server**:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## Test the API

Once running, test the health endpoint:
```bash
curl http://localhost:8000/health
```

Test ingestion endpoint:
```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/octocat/Hello-World"}'
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Command to run
source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000