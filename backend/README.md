# Owlivia Backend

The Owlivia backend is a FastAPI application that powers the STEM Graduate Advising Assistant.

It provides:

- RAG-based advising chat
- FAU source citations
- Health monitoring
- Prototype authentication
- Feedback submission
- LanceDB retrieval
- Local Qwen generation
- Lightweight Render deployment

## Main Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Checks backend and RAG status |
| `POST` | `/api/chat` | Returns an advising answer with FAU sources |
| `POST` | `/api/feedback` | Submits feedback |
| `POST` | `/api/auth/login` | Prototype authentication |
| `GET` | `/docs` | Swagger API documentation |

## Local Setup

From the `backend` folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Full Local RAG Mode

```powershell
$env:ENVIRONMENT = "local"
$env:RAG_GENERATION_MODE = "local"
$env:RAG_DENSE_ENABLED = "true"

python -m uvicorn app.main:app --reload
```

Local Swagger:

```text
http://127.0.0.1:8000/docs
```

### Lightweight Render Mode

```powershell
$env:ENVIRONMENT = "local"
$env:RAG_GENERATION_MODE = "extractive"
$env:RAG_DENSE_ENABLED = "false"

python -m uvicorn app.main:app --reload
```

This mode uses:

- LanceDB BM25 retrieval
- Intent-aware reranking
- Extractive answer generation
- No Qwen loading
- No dense embedding model

## Run Tests

```powershell
python -m pytest -q
```

## Render Deployment

Render settings:

| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Branch | `main` |
| Root Directory | `backend` |
| Health Check Path | `/api/health` |

Build command:

```bash
python -m pip install --upgrade pip && python -m pip install -r requirements-render.txt
```

Start command:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```text
PYTHON_VERSION=3.12.8
ENVIRONMENT=production
RAG_GENERATION_MODE=extractive
RAG_DENSE_ENABLED=false
ALLOWED_ORIGINS=https://owlivia.vercel.app
```

## Production Links

- API: `https://YOUR-RENDER-URL.onrender.com`
- Health: `https://YOUR-RENDER-URL.onrender.com/api/health`
- Swagger: `https://YOUR-RENDER-URL.onrender.com/docs`

Do not commit API keys, access tokens, or other secrets.