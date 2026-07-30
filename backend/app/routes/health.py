"""Health-check route for the Owlivia backend."""

from fastapi import APIRouter

from app.config import settings
from app.rag.retriever import get_table
from app.schemas import HealthResponse


router = APIRouter()


def _lancedb_is_ready() -> bool:
    """Confirm that the local LanceDB table can be opened and read."""

    try:
        table = get_table()
        table.count_rows()
        return True
    except Exception:
        return False


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return the current backend and RAG service status."""

    database_ready = _lancedb_is_ready()

    if database_ready:
        retrieval_status = (
            "hybrid"
            if settings.rag_dense_enabled
            else "bm25"
        )
    else:
        retrieval_status = "unavailable"

    generation_mode = (
        settings.rag_generation_mode
        .strip()
        .lower()
    )

    llm_status = {
        "local": "qwen-local",
        "gemini": "gemini",
        "extractive": "extractive",
    }.get(generation_mode, "extractive")

    services = {
        "backend": "online",
        "database": (
            "connected"
            if database_ready
            else "unavailable"
        ),
        "retrieval": retrieval_status,
        "llm": llm_status,
    }

    return HealthResponse(
        status=(
            "online"
            if database_ready
            else "degraded"
        ),
        app=settings.app_name,
        environment=settings.environment,
        services=services,
    )