from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user_id
from app.schemas import ChatRequest, ChatResponse
from app.services import (
    generate_answer,
    new_id,
    retrieve_advising_context,
)


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def submit_chat_question(
    request: ChatRequest,
    _user_id: Annotated[str, Depends(get_current_user_id)],
) -> ChatResponse:
    """Retrieve FAU EECS context and generate an advising response."""

    retrieval = retrieve_advising_context(
        request.question,
        request.top_k,
    )

    answer = generate_answer(
        request.question,
        retrieval,
    )

    return ChatResponse(
        response_id=new_id(),
        session_id=request.session_id or new_id(),
        answer=answer,
        sources=retrieval.sources,
        confidence_status=retrieval.confidence_status,
        retrieval_mode=retrieval.mode,
        escalation_recommended=not retrieval.reliable,
    )