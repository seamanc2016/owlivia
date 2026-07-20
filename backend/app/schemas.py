from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class Source(BaseModel):
    document_id: str
    title: str
    url: str | None = None
    category: str | None = None
    excerpt: str | None = None
    relevance_score: float | None = Field(default=None, ge=0, le=1)
    updated_at: datetime | None = None


class HealthResponse(BaseModel):
    status: Literal["online", "degraded"]
    app: str
    environment: str
    services: dict[str, str]


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=10)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Question cannot be empty or contain only whitespace.")
        return normalized


class ChatResponse(BaseModel):
    response_id: UUID
    session_id: UUID
    answer: str
    sources: list[Source]
    confidence_status: Literal["prototype", "low", "medium", "high"]
    retrieval_mode: Literal["placeholder", "connected"]
    escalation_recommended: bool = False


class AuthVerifyResponse(BaseModel):
    authenticated: bool
    user_id: str
    message: str


class FeedbackRequest(BaseModel):
    response_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class FeedbackResponse(BaseModel):
    feedback_id: UUID
    response_id: UUID
    received: bool
    message: str
    created_at: datetime

