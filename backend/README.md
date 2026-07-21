# Owlivia Backend

The Owlivia backend is a FastAPI service that answers FAU EECS advising questions using a connected RAG pipeline.

It retrieves relevant department documents from LanceDB, reranks the results, generates a grounded answer with Qwen, and returns supporting sources to the frontend.

## Features

- FastAPI backend
- LanceDB document retrieval
- Dense and full-text search
- Weighted reciprocal-rank fusion
- Intent-aware reranking
- Exact course-code matching
- Qwen answer generation
- Grounding checks for numbers and course codes
- Source citations, confidence, and escalation status
- Automated API and retrieval tests

## Setup

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

## Run the Backend

```powershell
python -m uvicorn app.main:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

For protected routes, use:

```text
Bearer week3-prototype-token
```

## Main Routes

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/health` | Check backend status |
| `GET` | `/api/auth/verify` | Verify the prototype token |
| `POST` | `/api/chat` | Retrieve sources and answer a question |
| `POST` | `/api/feedback` | Submit response feedback |

## Example Chat Request

```json
{
  "question": "What are the prerequisites for CAP 4630?",
  "top_k": 5
}
```

The response includes:

- The generated answer
- Retrieved FAU EECS sources
- Confidence status
- Retrieval mode
- Escalation recommendation

Example answer:

```text
The prerequisite for CAP 4630 is COP 3530.
```

## RAG Pipeline

Each question goes through:

1. Query classification and expansion
2. Dense and full-text retrieval
3. Weighted reciprocal-rank fusion
4. Intent-aware reranking
5. Relevant context selection
6. Qwen answer generation
7. Grounding validation
8. Source and confidence formatting

The backend runs fresh retrieval for every request and does not use shared global conversation state.

## Run Tests

```powershell
python -m pytest -q
```

Current result:

```text
12 passed
```

## Current Limitations

- Supabase authentication is not connected yet.
- Chat history is not stored.
- Feedback is validated but not stored.
- The Qwen model currently runs locally.
- The backend has not yet been deployed.