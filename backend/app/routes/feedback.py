from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user_id
from app.schemas import FeedbackRequest, FeedbackResponse
from app.services import new_id

router = APIRouter()


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_feedback(
    request: FeedbackRequest,
    _user_id: Annotated[str, Depends(get_current_user_id)],
) -> FeedbackResponse:
    """Validate feedback and return the record shape expected from Supabase."""
    return FeedbackResponse(
        feedback_id=new_id(),
        response_id=request.response_id,
        received=True,
        message="Feedback validated. Supabase persistence is the next integration step.",
        created_at=datetime.now(timezone.utc),
    )

