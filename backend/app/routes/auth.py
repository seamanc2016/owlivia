from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user_id
from app.schemas import AuthVerifyResponse

router = APIRouter()


@router.get("/verify", response_model=AuthVerifyResponse)
def verify_auth_token(
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> AuthVerifyResponse:
    """Verify a token-shaped header until Supabase validation is connected."""
    return AuthVerifyResponse(
        authenticated=True,
        user_id=user_id,
        message="Prototype Bearer token accepted. Replace with Supabase verification.",
    )

