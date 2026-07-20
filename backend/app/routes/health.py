from fastapi import APIRouter

from app.config import settings
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    database_ready = bool(settings.supabase_url and settings.supabase_service_role_key)
    vector_ready = bool(settings.pinecone_api_key)
    llm_ready = bool(settings.llm_provider and settings.llm_api_key)

    services = {
        "backend": "online",
        "database": "configured" if database_ready else "not_configured",
        "retrieval": "configured" if vector_ready else "placeholder",
        "llm": "configured" if llm_ready else "placeholder",
    }

    return HealthResponse(
        status="online" if database_ready and vector_ready and llm_ready else "degraded",
        app=settings.app_name,
        environment=settings.environment,
        services=services,
    )

