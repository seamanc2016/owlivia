from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user_id
from app.schemas import ChatRequest, ChatResponse
from app.services import new_id, process_chat_request


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def submit_chat_question(
    request: ChatRequest,
    _user_id: Annotated[str, Depends(get_current_user_id)],
) -> ChatResponse:
    """Retrieve FAU EECS context and generate an advising response."""

    result = process_chat_request(request)

    return ChatResponse(
        response_id=new_id(),
        session_id=result.session_id,
        answer=result.answer,
        sources=result.sources,
        confidence_status=result.confidence_status,
        retrieval_mode=result.retrieval_mode,
        escalation_recommended=result.escalation_recommended,
        response_type=result.response_type,
        pending_slots=result.pending_slots,
    )
