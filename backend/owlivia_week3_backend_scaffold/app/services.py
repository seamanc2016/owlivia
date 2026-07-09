from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.schemas import Source


@dataclass(frozen=True)
class RetrievalResult:
    """Stable handoff object for the retrieval pipeline."""

    sources: list[Source]
    reliable: bool
    mode: Literal["placeholder", "connected"]


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "corpus_chunks.csv"


def _clean_text(value: object) -> str:
    """Convert missing CSV values into clean strings."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _short_excerpt(text: str, max_length: int = 500) -> str:
    """Return a readable excerpt for the API response."""
    text = " ".join(text.split())
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


@lru_cache(maxsize=1)
def _load_retrieval_index():
    """Load corpus_chunks.csv and build a TF-IDF search index once."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {DATA_PATH}. Copy the RAG data folder into the backend project."
        )

    df = pd.read_csv(DATA_PATH).fillna("")

    required_columns = {"doc_id", "chunk_text", "text", "title"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"corpus_chunks.csv is missing columns: {sorted(missing_columns)}")

    search_texts = (
        df.get("title", "").astype(str)
        + " "
        + df.get("course_code", "").astype(str)
        + " "
        + df.get("document_type", "").astype(str)
        + " "
        + df.get("chunk_text", "").astype(str)
        + " "
        + df.get("text", "").astype(str)
    )

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=20000,
    )
    matrix = vectorizer.fit_transform(search_texts)

    return df, vectorizer, matrix


def retrieve_advising_context(question: str, top_k: int = 5) -> RetrievalResult:
    """Search the EECS corpus chunks and return source metadata for Owlivia."""
    df, vectorizer, matrix = _load_retrieval_index()

    query_vector = vectorizer.transform([question])
    scores = cosine_similarity(query_vector, matrix).flatten()

    if len(scores) == 0:
        return RetrievalResult(sources=[], reliable=False, mode="connected")

    top_indices = scores.argsort()[::-1][:top_k]

    sources: list[Source] = []
    best_score = float(scores[top_indices[0]]) if len(top_indices) else 0.0

    for index in top_indices:
        score = float(scores[index])

        # Skip totally unrelated zero-score matches.
        if score <= 0:
            continue

        row = df.iloc[index]

        title = _clean_text(row.get("title"))
        course_code = _clean_text(row.get("course_code"))
        file_name = _clean_text(row.get("file_name"))

        display_title = title or course_code or file_name or "EECS advising source"

        url = (
            _clean_text(row.get("source_page"))
            or _clean_text(row.get("linked_file_or_page"))
            or None
        )

        category = _clean_text(row.get("document_type")) or None
        excerpt = _clean_text(row.get("chunk_text")) or _clean_text(row.get("text"))

        sources.append(
            Source(
                document_id=_clean_text(row.get("parent_doc_id"))
                or _clean_text(row.get("doc_id")),
                title=display_title,
                url=url,
                category=category,
                excerpt=_short_excerpt(excerpt),
                relevance_score=round(score, 4),
            )
        )

    reliable = best_score >= 0.12 and len(sources) > 0

    return RetrievalResult(
        sources=sources,
        reliable=reliable,
        mode="connected",
    )


def generate_answer(question: str, retrieval: RetrievalResult) -> str:
    """Generate a temporary sourced answer until the final LLM is connected."""
    if not retrieval.sources:
        return (
            "I could not find a strong matching EECS source for that question yet. "
            "The retrieval system is connected, but this question may need a human advisor "
            "or a broader document search."
        )

    top_source = retrieval.sources[0]
    source_titles = ", ".join(source.title for source in retrieval.sources[:3])

    return (
        f'I found relevant EECS information for your question: "{question}". '
        f'The strongest match is "{top_source.title}"'
        f"{f' ({top_source.url})' if top_source.url else ''}. "
        f"Other related sources include: {source_titles}. "
        "This is the retrieval-connected prototype response; the final version can use these "
        "sources with an LLM to write a more complete advising answer."
    )


def new_id() -> UUID:
    return uuid4()