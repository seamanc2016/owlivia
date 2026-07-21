"""Application services for Owlivia retrieval and answer generation."""

from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID, uuid4

import pandas as pd

from app.rag import generator as rag_generator
from app.rag.reranker import retrieve_and_rerank
from app.schemas import Source


@dataclass(frozen=True)
class RetrievalResult:
    """Internal handoff between retrieval and answer generation."""

    sources: list[Source]
    context_chunks: list[str]
    reliable: bool
    mode: Literal["placeholder", "connected"]
    confidence_status: Literal["low", "medium", "high"]


def _clean_value(value: Any) -> str | None:
    """Convert empty and null-like metadata into None."""

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    cleaned = " ".join(str(value).split())

    if not cleaned or cleaned.lower() in {
        "nan",
        "none",
        "null",
    }:
        return None

    return cleaned


def _clean_url(value: Any) -> str | None:
    """Return a value only when it is a valid HTTP source URL."""

    cleaned = _clean_value(value)

    if not cleaned:
        return None

    if cleaned.lower().startswith(
        (
            "http://",
            "https://",
        )
    ):
        return cleaned

    return None


def _build_excerpt(
    value: Any,
    max_length: int = 500,
) -> str | None:
    """Create a short source excerpt for the API response."""

    cleaned = _clean_value(value)

    if not cleaned:
        return None

    if len(cleaned) <= max_length:
        return cleaned

    shortened = cleaned[: max_length - 3]

    if " " in shortened:
        shortened = shortened.rsplit(" ", 1)[0]

    return f"{shortened}..."


def _normalize_relevance_score(
    score: Any,
    maximum_score: float,
) -> float | None:
    """Normalize a reranker score into the API's zero-to-one range."""

    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        return None

    if maximum_score <= 0:
        return None

    normalized = numeric_score / maximum_score

    return round(
        max(
            0.0,
            min(1.0, normalized),
        ),
        4,
    )


def _row_to_source(
    row: pd.Series,
    maximum_score: float,
) -> Source:
    """Convert one internal document into a public Source object."""

    document_id = (
        _clean_value(row.get("doc_id"))
        or f"retrieved-source-{uuid4()}"
    )

    title = (
        _clean_value(row.get("title"))
        or _clean_value(row.get("link_text"))
        or _clean_value(row.get("file_name"))
        or "FAU EECS source"
    )

    url = (
        _clean_url(row.get("url"))
        or _clean_url(row.get("source_page"))
    )

    category = (
        _clean_value(row.get("document_type"))
        or _clean_value(row.get("resource_type"))
        or _clean_value(row.get("source_kind"))
    )

    excerpt_value = _clean_value(row.get("snippet"))

    if not excerpt_value:
        excerpt_value = _clean_value(row.get("text"))

    return Source(
        document_id=document_id,
        title=title,
        url=url,
        category=category,
        excerpt=_build_excerpt(excerpt_value),
        relevance_score=_normalize_relevance_score(
            row.get("rag_rerank_score"),
            maximum_score,
        ),
    )


def _get_confidence_status(
    documents: pd.DataFrame,
    context_chunks: list[str],
) -> Literal["low", "medium", "high"]:
    """Estimate retrieval confidence from hybrid-search agreement."""

    if documents.empty or not context_chunks:
        return "low"

    top_document = documents.iloc[0]

    bm25_rank = top_document.get("bm25_rank")
    dense_rank = top_document.get("dense_rank")

    has_bm25 = (
        bm25_rank is not None
        and not pd.isna(bm25_rank)
    )

    has_dense = (
        dense_rank is not None
        and not pd.isna(dense_rank)
    )

    if has_bm25 and has_dense:
        return "high"

    if has_bm25 or has_dense:
        return "medium"

    return "low"


def retrieve_advising_context(
    question: str,
    top_k: int = 5,
) -> RetrievalResult:
    """Retrieve and rerank relevant FAU EECS advising information."""

    rag_result = retrieve_and_rerank(
        question=question,
        top_k=top_k,
    )

    documents = rag_result.documents

    context_chunks = [
        line.strip()
        for line in rag_result.hidden_context.splitlines()
        if line.strip()
    ]

    if documents.empty:
        return RetrievalResult(
            sources=[],
            context_chunks=[],
            reliable=False,
            mode="connected",
            confidence_status="low",
        )

    maximum_score = float(
        documents["rag_rerank_score"].max()
    )

    sources = [
        _row_to_source(
            row=row,
            maximum_score=maximum_score,
        )
        for _, row in documents.iterrows()
    ]

    confidence_status = _get_confidence_status(
        documents=documents,
        context_chunks=context_chunks,
    )

    return RetrievalResult(
        sources=sources,
        context_chunks=context_chunks,
        reliable=confidence_status in {
            "medium",
            "high",
        },
        mode="connected",
        confidence_status=confidence_status,
    )


def generate_answer(
    question: str,
    retrieval: RetrievalResult,
) -> str:
    """Generate an answer using internal retrieved context."""

    return rag_generator.generate(
        question=question,
        context_chunks=retrieval.context_chunks,
    )


def new_id() -> UUID:
    """Create a UUID for responses and sessions."""

    return uuid4()