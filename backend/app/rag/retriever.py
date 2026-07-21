"""Hybrid LanceDB retrieval for the Owlivia advising assistant."""

from functools import lru_cache
from typing import Any

import lancedb
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from app.config import settings


# Stored database fields that should be returned with each search result.
SEARCH_COLUMNS = [
    "doc_id",
    "text",
    "bm25_text",
    "source_kind",
    "resource_type",
    "link_text",
    "url",
    "source_page",
    "saved_path",
    "file_name",
    "file_extension",
    "chunk_index",
    "text_hash",
]


@lru_cache(maxsize=1)
def get_database() -> Any:
    """Connect to the local LanceDB database once per backend process."""

    database_path = settings.lancedb_path

    if not database_path.exists():
        raise FileNotFoundError(
            f"LanceDB directory was not found: {database_path}"
        )

    return lancedb.connect(str(database_path))


@lru_cache(maxsize=1)
def get_table() -> Any:
    """Open and cache the FAU EECS resources table."""

    database = get_database()

    try:
        return database.open_table(settings.lancedb_table_name)
    except Exception as exc:
        raise RuntimeError(
            "Unable to open LanceDB table "
            f"'{settings.lancedb_table_name}' from "
            f"'{settings.lancedb_path}'."
        ) from exc


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the embedding model used to build the stored vectors."""

    return SentenceTransformer(settings.embedding_model_name)


def get_database_summary() -> dict[str, Any]:
    """Return basic information about the connected LanceDB table."""

    table = get_table()

    return {
        "database_path": str(settings.lancedb_path),
        "table_name": table.name,
        "row_count": table.count_rows(),
        "schema": str(table.schema),
        "indices": [str(index) for index in table.list_indices()],
    }


def encode_query(question: str) -> np.ndarray:
    """Convert a question into a normalized query vector."""

    normalized_question = question.strip()

    if not normalized_question:
        raise ValueError("The retrieval question cannot be empty.")

    query_vector = get_embedding_model().encode(
        [normalized_question],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]

    return query_vector.astype(np.float32)


def _keep_result_columns(
    results: pd.DataFrame,
    generated_columns: list[str],
) -> pd.DataFrame:
    """Keep stored metadata plus search-generated score fields."""

    selected_columns = [
        column
        for column in SEARCH_COLUMNS + generated_columns
        if column in results.columns
    ]

    return results[selected_columns].copy()


def dense_search(question: str, top_k: int) -> pd.DataFrame:
    """Run semantic vector search against the stored MiniLM vectors."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    query_vector = encode_query(question)

    results = (
        get_table()
        .search(
            query_vector,
            vector_column_name="vector",
            query_type="vector",
        )
        .distance_type("cosine")
        .limit(top_k)
        .to_pandas()
    )

    # LanceDB adds _distance after the vector query executes.
    results = _keep_result_columns(
        results,
        generated_columns=["_distance"],
    )

    results["dense_rank"] = range(1, len(results) + 1)

    return results


def bm25_search(question: str, top_k: int) -> pd.DataFrame:
    """Run keyword-based full-text search against bm25_text."""

    normalized_question = question.strip()

    if not normalized_question:
        raise ValueError("The retrieval question cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    results = (
        get_table()
        .search(
            normalized_question,
            query_type="fts",
            fts_columns="bm25_text",
        )
        .limit(top_k)
        .to_pandas()
    )

    # LanceDB adds _score after the FTS query executes.
    results = _keep_result_columns(
        results,
        generated_columns=["_score"],
    )

    results["bm25_rank"] = range(1, len(results) + 1)

    return results


def _metadata_from_row(row: pd.Series) -> dict[str, Any]:
    """Extract stored source metadata from a search-result row."""

    return {
        column: row.get(column)
        for column in SEARCH_COLUMNS
        if column in row.index
    }


def _is_useful_value(value: Any) -> bool:
    """Return whether a metadata value contains useful content."""

    if value is None:
        return False

    value_text = str(value).strip()

    return bool(value_text) and value_text.lower() not in {
        "nan",
        "none",
        "null",
    }


def _get_fusion_key(row: pd.Series) -> str:
    """Create one identity for duplicate copies of the same source chunk."""

    chunk_index = str(row.get("chunk_index", "")).strip()

    # Prefer filename because the database may contain multiple records that
    # point to the same downloaded PDF.
    file_name = str(row.get("file_name", "")).strip().lower()
    if _is_useful_value(file_name):
        return f"file:{file_name}|chunk:{chunk_index}"

    url = str(row.get("url", "")).strip().lower()
    if _is_useful_value(url):
        return f"url:{url}|chunk:{chunk_index}"

    text_hash = str(row.get("text_hash", "")).strip().lower()
    if _is_useful_value(text_hash):
        return f"hash:{text_hash}"

    document_id = str(row.get("doc_id", "")).strip()
    return f"doc:{document_id}"


def _merge_missing_metadata(
    existing_record: dict[str, Any],
    row: pd.Series,
) -> None:
    """Fill missing source metadata using another duplicate record."""

    for column in SEARCH_COLUMNS:
        current_value = existing_record.get(column)
        incoming_value = row.get(column)

        if not _is_useful_value(current_value) and _is_useful_value(
            incoming_value
        ):
            existing_record[column] = incoming_value


def reciprocal_rank_fusion(
    dense_results: pd.DataFrame,
    bm25_results: pd.DataFrame,
    top_k: int,
) -> pd.DataFrame:
    """Combine dense and BM25 rankings using weighted RRF.

    Duplicate database records representing the same file and chunk are
    merged before the final scores are calculated.
    """

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    fused: dict[str, dict[str, Any]] = {}

    result_sets = [
        (dense_results, "dense_rank"),
        (bm25_results, "bm25_rank"),
    ]

    for results, rank_column in result_sets:
        for fallback_rank, (_, row) in enumerate(
            results.iterrows(),
            start=1,
        ):
            row_rank = row.get(rank_column)

            if row_rank is None or pd.isna(row_rank):
                rank = fallback_rank
            else:
                rank = int(row_rank)

            fusion_key = _get_fusion_key(row)

            if fusion_key not in fused:
                fused[fusion_key] = _metadata_from_row(row)
                fused[fusion_key]["dense_rank"] = None
                fused[fusion_key]["bm25_rank"] = None
                fused[fusion_key]["dense_distance"] = None
                fused[fusion_key]["bm25_score"] = None
            else:
                _merge_missing_metadata(fused[fusion_key], row)

            current_rank = fused[fusion_key].get(rank_column)

            # Keep only the strongest rank from each retrieval method.
            if current_rank is None or rank < current_rank:
                fused[fusion_key][rank_column] = rank

            # Lower cosine distance is better.
            if "_distance" in row.index and pd.notna(row["_distance"]):
                distance = float(row["_distance"])
                current_distance = fused[fusion_key].get(
                    "dense_distance"
                )

                if (
                    current_distance is None
                    or distance < current_distance
                ):
                    fused[fusion_key]["dense_distance"] = distance

            # Higher BM25 score is better.
            if "_score" in row.index and pd.notna(row["_score"]):
                score = float(row["_score"])
                current_score = fused[fusion_key].get("bm25_score")

                if current_score is None or score > current_score:
                    fused[fusion_key]["bm25_score"] = score

    if not fused:
        return pd.DataFrame()

    # Calculate one RRF contribution per retrieval method after duplicates
    # have been merged. This prevents duplicate rows from inflating scores.
    for record in fused.values():
        rrf_score = 0.0

        dense_rank = record.get("dense_rank")
        if dense_rank is not None:
            rrf_score += (
                settings.rag_dense_weight
                / (settings.rag_rrf_k + dense_rank)
            )

        bm25_rank = record.get("bm25_rank")
        if bm25_rank is not None:
            rrf_score += (
                settings.rag_bm25_weight
                / (settings.rag_rrf_k + bm25_rank)
            )

        record["rrf_score"] = float(rrf_score)

    combined = pd.DataFrame(fused.values())

    combined = (
        combined
        .sort_values(
            by="rrf_score",
            ascending=False,
        )
        .head(top_k)
        .reset_index(drop=True)
    )

    combined.insert(
        0,
        "rank",
        range(1, len(combined) + 1),
    )

    return combined


def hybrid_search(
    question: str,
    top_k: int | None = None,
    candidate_pool: int | None = None,
) -> pd.DataFrame:
    """Run dense and BM25 retrieval and return weighted RRF results."""

    normalized_question = question.strip()

    if not normalized_question:
        raise ValueError("The retrieval question cannot be empty.")

    requested_top_k = (
        top_k
        if top_k is not None
        else settings.rag_top_k
    )

    retrieval_pool = (
        candidate_pool
        if candidate_pool is not None
        else settings.rag_retrieval_pool
    )

    if requested_top_k < 1:
        raise ValueError("top_k must be at least 1.")

    if retrieval_pool < requested_top_k:
        retrieval_pool = requested_top_k

    dense_results = dense_search(
        normalized_question,
        retrieval_pool,
    )

    bm25_results = bm25_search(
        normalized_question,
        retrieval_pool,
    )

    return reciprocal_rank_fusion(
        dense_results=dense_results,
        bm25_results=bm25_results,
        top_k=requested_top_k,
    )