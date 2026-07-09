# Owlivia Week 3 Backend Scaffold

This FastAPI scaffold refines the Week 2 routes and defines stable contracts for the retrieval pipeline, frontend, Supabase, and the eventual LLM.

## Routes

| Method | Route | Purpose | Authentication |
|---|---|---|---|
| `GET` | `/api/health` | Report backend and integration readiness | No |
| `POST` | `/api/chat` | Validate a question and return a prototype sourced response | Bearer token |
| `GET` | `/api/auth/verify` | Validate the current prototype token format | Bearer token |
| `POST` | `/api/feedback` | Validate feedback and return its future database shape | Bearer token |

The prototype accepts any nonempty `Bearer` token. Supabase verification is not connected yet.

## Run on Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to test the API. In Swagger, click **Authorize** and enter `Bearer week3-prototype-token`.

## Run tests

```powershell
pytest -q
```

## Chat contract

Example request:

```json
{
  "question": "What are the graduate credit requirements?",
  "session_id": null,
  "top_k": 5
}
```

The response returns `response_id`, `session_id`, `answer`, `sources`, `confidence_status`, `retrieval_mode`, and `escalation_recommended`. Each source includes a document ID, title, optional URL/category/excerpt/update date, and relevance score.

## Integration handoff

- Retrieval: replace the body of `app.services.retrieve_advising_context` and preserve its inputs and output fields.
- Frontend: set `ALLOWED_ORIGINS` to the frontend URL and consume the documented response fields.
- Authentication: replace `app.dependencies.get_current_user_id` with Supabase JWT verification.
- Persistence: use `docs/database_schema.sql` when the Supabase project is ready.

The current retrieval, generation, authentication, and persistence behavior is intentionally mocked. The API contracts and validation can be tested now without external credentials.
