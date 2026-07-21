"""Intent-aware reranking and context construction for Owlivia."""

from dataclasses import dataclass
from typing import Any
import re

import pandas as pd

from app.config import settings
from app.rag.retriever import hybrid_search


RAG_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "could",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "need",
    "needed",
    "of",
    "on",
    "or",
    "should",
    "the",
    "their",
    "there",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "will",
    "with",
    "would",
    "you",
    "your",
    "about",
    "related",
    "information",
    "student",
}


RETRIEVAL_EXPANSIONS_BY_INTENT = {
    "course_recommendation": [
        "course listing",
        "course offerings",
        "prerequisite",
        "credits",
        "CAP",
        "CDA",
        "CEN",
        "CIS",
        "COP",
        "COT",
        "EEL",
        "EEE",
    ],
    "certificate_requirements": [
        "certificate",
        "requirements",
        "required courses",
        "credits",
        "worksheet",
        "program sheet",
        "application",
    ],
    "degree_requirements": [
        "degree requirements",
        "program sheet",
        "program worksheet",
        "required credits",
        "curriculum",
        "graduate program",
    ],
    "person_lookup": [
        "department chair",
        "director",
        "advisor",
        "coordinator",
        "faculty",
    ],
    "forms": [
        "form",
        "worksheet",
        "application",
        "degree audit",
        "plan of study",
        "requirements",
    ],
    "general": [
        "computer science",
        "electrical engineering",
        "department",
        "program",
        "requirements",
    ],
}


KEYWORD_EXPANSIONS = {
    "ai": ["artificial intelligence", "machine learning"],
    "ml": ["machine learning", "artificial intelligence"],
    "big data": ["big data analytics", "data analytics"],
    "cyber": ["cybersecurity", "cyber security"],
    "computer science": ["CS", "CSE", "MSCS"],
    "computer engineering": ["computer engineering", "CpE", "COEN"],
    "electrical engineering": ["electrical engineering", "EE", "EEL"],
    "credits": ["credit hours", "total credits", "required credits"],
}


@dataclass(frozen=True)
class RerankResult:
    """Output from retrieval, reranking, and context construction."""

    retrieval_query: str
    intent: str
    documents: pd.DataFrame
    hidden_context: str


def normalize_text(value: Any) -> str:
    """Normalize whitespace and remove null-like values."""

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    cleaned = " ".join(str(value).replace("\x00", " ").split())

    if cleaned.lower() in {"nan", "none", "null"}:
        return ""

    return cleaned

def clean_document_content(
    content: str,
    title: str = "",
    file_name: str = "",
) -> str:
    """Remove retrieval metadata and paths from document content."""

    cleaned = normalize_text(content)

    # Remove URLs and copied local paths.
    cleaned = re.sub(
        r"https?://\S+",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"DepCourseInfo\\\S+",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove database labels that should not be given to the LLM.
    cleaned = re.sub(
        r"\b("
        r"program_or_advising_worksheet|"
        r"external_link|"
        r"downloaded_resource|"
        r"course_listing"
        r")\b",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove null markers, including strings such as "nanThe".
    cleaned = re.sub(
        r"\b(?:nan|none|null)(?=[A-Z])",
        " ",
        cleaned,
    )

    cleaned = re.sub(
        r"\b(?:nan|none|null)\b",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Avoid repeating source titles at the beginning of snippets.
    for repeated_value in [title, file_name]:
        repeated_value = normalize_text(repeated_value)

        if repeated_value:
            cleaned = re.sub(
                re.escape(repeated_value),
                " ",
                cleaned,
                flags=re.IGNORECASE,
            )

    return normalize_text(cleaned)

def rag_terms(text: str) -> list[str]:
    """Return useful lowercase words for lexical scoring."""

    words = re.findall(
        r"[A-Za-z][A-Za-z0-9]+",
        str(text).lower(),
    )

    return [
        word
        for word in words
        if word not in RAG_STOPWORDS and len(word) > 2
    ]


def classify_rag_intent(question: str) -> str:
    """Classify a question into a broad advising retrieval intent."""

    lowered = normalize_text(question).lower()

    if "certificate" in lowered or "certification" in lowered:
        return "certificate_requirements"

    if any(
        term in lowered
        for term in [
            "form",
            "worksheet",
            "application",
            "audit",
            "plan of study",
        ]
    ):
        return "forms"

    if any(
        term in lowered
        for term in [
            "chair",
            "director",
            "advisor",
            "coordinator",
            "dean",
        ]
    ):
        return "person_lookup"

    if any(
        term in lowered
        for term in [
            "master",
            "masters",
            "m.s.",
            "ms ",
            "degree",
            "credit",
            "credits",
            "requirements",
            "program requirements",
            "phd",
            "doctoral",
        ]
    ):
        return "degree_requirements"

    if any(
        term in lowered
        for term in [
            "recommend",
            "class",
            "classes",
            "course",
            "courses",
            "take",
            "prerequisite",
            "fall",
            "spring",
            "summer",
        ]
    ):
        return "course_recommendation"

    return "general"


def improve_query_for_hybrid_search(
    original_query: str,
    max_extra_terms: int = 24,
) -> str:
    """Expand a question for retrieval without changing the user-facing text."""

    original_query = normalize_text(original_query)

    if not original_query:
        raise ValueError("The retrieval question cannot be empty.")

    lowered = original_query.lower()
    intent = classify_rag_intent(original_query)
    extra_terms: list[str] = []

    requested_course_code = extract_course_code(original_query)

    # Exact course-code questions should stay focused. Adding every EECS
    # prefix can dilute the lexical query and cause general worksheets to
    # outrank the requested course document.
    if requested_course_code and intent == "course_recommendation":
        targeted_terms = [
            "course description",
            "catalog description",
            "prerequisite",
            "syllabus",
            "credits",
        ]

        for term in targeted_terms:
            if term.lower() not in lowered:
                extra_terms.append(term)

        return f"{original_query} {' '.join(extra_terms)}"

    for term in RETRIEVAL_EXPANSIONS_BY_INTENT.get(intent, []):
        if (
            term.lower() not in lowered
            and term.lower() not in {
                existing.lower()
                for existing in extra_terms
            }
        ):
            extra_terms.append(term)

    for trigger, expansions in KEYWORD_EXPANSIONS.items():
        if trigger in lowered:
            for term in expansions:
                if (
                    term.lower() not in lowered
                    and term.lower() not in {
                        existing.lower()
                        for existing in extra_terms
                    }
                ):
                    extra_terms.append(term)

    extra_terms = extra_terms[:max_extra_terms]

    if not extra_terms:
        return original_query

    return f"{original_query} {' '.join(extra_terms)}"


def extract_course_code(text: str) -> str:
    """Extract an EECS-style course code from metadata or document text."""

    match = re.search(
        r"\b(CAP|CDA|CEN|CGS|CIS|CNT|COP|COT|EEE|EEL|EGN)"
        r"\s*[-_ ]?\s*(\d{4}[A-Z]?)\b",
        str(text),
        flags=re.IGNORECASE,
    )

    if not match:
        return ""

    return f"{match.group(1).upper()} {match.group(2).upper()}"


def contains_course_code(
    text: str,
    course_code: str,
) -> bool:
    """Return whether text contains the requested course code exactly."""

    normalized_code = extract_course_code(course_code)

    if not normalized_code:
        return False

    prefix, number = normalized_code.split(" ", 1)

    pattern = (
        rf"\b{re.escape(prefix)}"
        rf"\s*[-_ ]?\s*{re.escape(number)}\b"
    )

    return re.search(
        pattern,
        str(text),
        flags=re.IGNORECASE,
    ) is not None


def row_to_document(row: pd.Series) -> dict[str, str]:
    """Convert a LanceDB result row into normalized document metadata."""

    raw_content = normalize_text(row.get("text"))
    link_text = normalize_text(row.get("link_text"))
    file_name = normalize_text(row.get("file_name"))

    title = link_text or file_name or "FAU EECS source"

    document_type = (
        normalize_text(row.get("resource_type"))
        or normalize_text(row.get("source_kind"))
    )

    content = clean_document_content(
        content=raw_content,
        title=title,
        file_name=file_name,
    )

    # Only inspect source identity fields for a course code. Searching the
    # worksheet body caused individual courses to be mistaken for its title.
    identity_text = " ".join(
        [
            title,
            file_name,
        ]
    )

    return {
        "doc_id": normalize_text(row.get("doc_id")),
        "content": content,
        "title": title,
        "document_type": document_type,
        "course_code": extract_course_code(identity_text),
        "file_name": file_name,
        "source": (
            normalize_text(row.get("url"))
            or normalize_text(row.get("source_page"))
        ),
        "chunk_index": normalize_text(row.get("chunk_index")),
    }


def intent_keywords(intent: str) -> list[str]:
    """Return important terms for each advising intent."""

    return {
        "course_recommendation": [
            "course",
            "prerequisite",
            "credits",
            "undergraduate",
            "graduate",
            "cap",
            "cda",
            "cen",
            "cis",
            "cop",
            "cot",
            "eel",
            "eee",
        ],
        "certificate_requirements": [
            "certificate",
            "requirements",
            "required",
            "credits",
            "courses",
            "worksheet",
            "application",
        ],
        "degree_requirements": [
            "degree",
            "requirements",
            "credits",
            "program",
            "curriculum",
            "worksheet",
            "graduate",
        ],
        "person_lookup": [
            "chair",
            "director",
            "coordinator",
            "advisor",
            "faculty",
        ],
        "forms": [
            "form",
            "worksheet",
            "application",
            "audit",
            "plan",
            "study",
        ],
        "general": [],
    }.get(intent, [])


def score_text_for_query(
    text: str,
    original_query: str,
    retrieval_query: str,
    intent: str,
) -> float:
    """Score text using query overlap and intent-oriented terms."""

    lowered = normalize_text(text).lower()

    original_terms = set(rag_terms(original_query))
    retrieval_terms = set(rag_terms(retrieval_query))
    query_terms = original_terms | retrieval_terms

    score = 0.0

    for term in query_terms:
        if term in lowered:
            score += 2.0

    for term in original_terms:
        if term in lowered:
            score += 1.5

    for term in intent_keywords(intent):
        if term.lower() in lowered:
            score += 1.25

    original_phrase = normalize_text(original_query).lower()

    if original_phrase and original_phrase in lowered:
        score += 8.0

    for irrelevant_term in [
        "patient",
        "diagnosis",
        "medication",
        "clinical procedure",
        "heart disease",
    ]:
        if irrelevant_term in lowered:
            score -= 8.0

    words = rag_terms(lowered)

    if len(words) >= 30:
        counts = {
            word: words.count(word)
            for word in set(words)
        }

        highest_count = max(counts.values(), default=0)

        if highest_count / len(words) > 0.18:
            score -= 6.0

    return score


def document_intent_boost(
    document: dict[str, str],
    original_query: str,
    intent: str,
) -> float:
    """Boost documents that match the requested program and intent."""

    query = normalize_text(original_query).lower()

    identity_text = " ".join(
        [
            document.get("title", ""),
            document.get("file_name", ""),
            document.get("document_type", ""),
            document.get("course_code", ""),
        ]
    ).lower()

    content_preview = document.get("content", "")[:1600].lower()
    combined = f"{identity_text} {content_preview}"

    boost = 0.0

    if intent == "degree_requirements":
        if any(
            term in identity_text
            for term in [
                "program worksheet",
                "program sheet",
                "worksheet",
            ]
        ):
            boost += 6.0

        computer_science_query = (
            "computer science" in query
            or "mscs" in query
            or "ms cs" in query
            or "m.s. in computer science" in query
        )

        if computer_science_query:
            standard_cs_source = any(
                term in identity_text
                for term in [
                    "ms-in-computer-science-program-worksheet",
                    "ms-cse-worksheet",
                ]
            )

            if standard_cs_source:
                boost += 20.0

            unrelated_cs_programs = [
                "minor in business",
                "information technology management",
                "cybersecurity",
                "data science",
                "data analytics",
                "computer engineering",
                "electrical engineering",
            ]

            for unrelated_program in unrelated_cs_programs:
                if (
                    unrelated_program in identity_text
                    and unrelated_program not in query
                ):
                    boost -= 18.0

        if "computer engineering" in query:
            if (
                "computer engineering" in identity_text
                or "coen" in identity_text
            ):
                boost += 18.0

        if "electrical engineering" in query:
            if (
                "electrical engineering" in identity_text
                or "ms-in-eel" in identity_text
            ):
                boost += 18.0

        if (
            "data science" in query
            and "data science" in identity_text
        ):
            boost += 18.0

        # Use the correct worksheet when the student provides a start term.
        if (
            "summer 2025" in query
            or "fall 2025" in query
            or "spring 2026" in query
            or "later" in query
        ):
            if "ms-cse-worksheet-new" in identity_text:
                boost += 12.0

            if (
                "ms-in-computer-science-program-worksheet"
                in identity_text
            ):
                boost -= 8.0

        if (
            "spring 2025" in query
            or "earlier" in query
        ):
            if (
                "ms-in-computer-science-program-worksheet"
                in identity_text
            ):
                boost += 12.0

            if "ms-cse-worksheet-new" in identity_text:
                boost -= 8.0

        if "phd" not in query and "doctoral" not in query:
            if (
                "phd" in identity_text
                or "doctoral" in identity_text
            ):
                boost -= 10.0

    elif intent == "certificate_requirements":
        if "certificate" in identity_text:
            boost += 10.0

        if any(
            term in combined
            for term in [
                "requirements",
                "required",
                "credits",
                "worksheet",
                "application",
            ]
        ):
            boost += 4.0

        if (
            "big data" in query
            and "big data" in identity_text
        ):
            boost += 10.0

        if (
            "artificial intelligence" in query
            or re.search(r"\bai\b", query)
        ):
            if (
                "artificial intelligence" in identity_text
                or "ai-certificate" in identity_text
            ):
                boost += 10.0

        if (
            "cyber" in query
            and "cyber" in identity_text
        ):
            boost += 10.0

    elif intent == "course_recommendation":
        requested_course_code = extract_course_code(original_query)
        document_course_code = normalize_text(
            document.get("course_code")
        ).upper()

        exact_identity_match = (
            bool(requested_course_code)
            and document_course_code == requested_course_code
        )

        exact_content_match = (
            bool(requested_course_code)
            and contains_course_code(
                document.get("content", ""),
                requested_course_code,
            )
        )

        if requested_course_code:
            if exact_identity_match:
                # A title or filename that identifies the exact course is
                # the strongest possible signal for course-code questions.
                boost += 60.0
            elif exact_content_match:
                # The course may appear inside a worksheet or course list,
                # which is relevant but weaker than a course-specific file.
                boost += 18.0
            else:
                boost -= 24.0

            if (
                "prerequisite" in query
                or "prerequisites" in query
            ):
                if exact_identity_match and "prerequisite" in combined:
                    boost += 16.0
                elif exact_identity_match:
                    boost += 6.0

            if (
                not exact_identity_match
                and any(
                    term in identity_text
                    for term in [
                        "program worksheet",
                        "program sheet",
                        "degree worksheet",
                        "minor in business",
                    ]
                )
            ):
                boost -= 18.0
        elif document.get("course_code"):
            boost += 8.0

        if "syllabus" in identity_text:
            boost += 3.0

        if (
            "phd" in identity_text
            or "doctoral" in identity_text
        ):
            boost -= 6.0

    elif intent == "forms":
        if any(
            term in identity_text
            for term in [
                "form",
                "worksheet",
                "application",
                "audit",
            ]
        ):
            boost += 8.0

    elif intent == "person_lookup":
        if any(
            term in combined
            for term in [
                "chair",
                "director",
                "advisor",
                "coordinator",
                "faculty",
            ]
        ):
            boost += 8.0

    return boost


def split_into_candidate_sentences(text: str) -> list[str]:
    """Split document text into manageable candidate snippets."""

    normalized = normalize_text(text)

    rough_parts = re.split(
        r"(?<=[.!?])\s+|\s{2,}|\s+[•●]\s+",
        normalized,
    )

    sentences: list[str] = []

    for part in rough_parts:
        cleaned = part.strip(" -\t\n\r")

        if 25 <= len(cleaned) <= 520:
            sentences.append(cleaned)
        elif len(cleaned) > 520:
            for start in range(0, len(cleaned), 360):
                chunk = cleaned[start : start + 520].strip()

                if len(chunk) >= 25:
                    sentences.append(chunk)

    return sentences


def select_relevant_snippet(
    document: dict[str, str],
    original_query: str,
    retrieval_query: str,
    intent: str,
    max_chars: int | None = None,
) -> str:
    """Select the strongest short passage from a retrieved document."""

    limit = max_chars or settings.rag_max_snippet_chars
    candidate_text = document.get("content", "")
    sentences = split_into_candidate_sentences(candidate_text)

    if not sentences:
        return normalize_text(candidate_text)[:limit]

    scored_sentences: list[tuple[float, str]] = []

    for sentence in sentences:
        score = score_text_for_query(
            sentence,
            original_query,
            retrieval_query,
            intent,
        )

        lowered_sentence = sentence.lower()
        requested_course_code = extract_course_code(original_query)

        if requested_course_code:
            if contains_course_code(
                sentence,
                requested_course_code,
            ):
                score += 24.0

                if (
                    "prerequisite" in normalize_text(
                        original_query
                    ).lower()
                    and "prerequisite" in lowered_sentence
                ):
                    score += 14.0

        if intent == "degree_requirements":
            if any(
                phrase in lowered_sentence
                for phrase in [
                    "degree requirements",
                    "minimum degree requirements",
                    "credit hours",
                    "credits required",
                    "thesis option",
                    "non-thesis option",
                    "plan of study",
                    "core courses",
                    "elective courses",
                ]
            ):
                score += 8.0

        if intent == "certificate_requirements":
            if any(
                phrase in lowered_sentence
                for phrase in [
                    "certificate requirements",
                    "required courses",
                    "credit hours",
                    "application",
                ]
            ):
                score += 8.0

        scored_sentences.append(
            (
                score,
                sentence,
            )
        )

    scored_sentences.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    selected: list[str] = []
    total_chars = 0

    for score, sentence in scored_sentences[:8]:
        if score <= 0 and selected:
            continue

        if sentence in selected:
            continue

        if (
            total_chars + len(sentence) > limit
            and selected
        ):
            continue

        selected.append(sentence)
        total_chars += len(sentence)

        if total_chars >= limit:
            break

    if not selected:
        selected = [sentences[0][:limit]]

    return normalize_text(
        " ".join(selected)
    )[:limit].rstrip()


def get_fused_base_score(row: pd.Series) -> float:
    """Read the RRF score from a fused retrieval row."""

    value = row.get("rrf_score")

    try:
        if value is not None and not pd.isna(value):
            return float(value)
    except (TypeError, ValueError):
        pass

    return 0.0


def source_identity(row: pd.Series) -> str:
    """Create a stable identity used to limit repeated source chunks."""

    file_name = normalize_text(row.get("file_name")).lower()

    if file_name:
        return f"file:{file_name}"

    url = normalize_text(row.get("url")).lower()

    if url:
        return f"url:{url}"

    return f"doc:{normalize_text(row.get('doc_id'))}"


def rerank_fused_results(
    fused_results: pd.DataFrame,
    original_query: str,
    retrieval_query: str,
    top_k: int,
    max_chunks_per_source: int = 1,
) -> pd.DataFrame:
    """Rerank RRF results using text relevance and intent boosts."""

    if fused_results.empty:
        return fused_results.copy()

    intent = classify_rag_intent(original_query)
    reranked_rows: list[dict[str, Any]] = []

    for _, row in fused_results.iterrows():
        document = row_to_document(row)

        searchable_text = " ".join(
            [
                document.get("title", ""),
                document.get("file_name", ""),
                document.get("course_code", ""),
                document.get("content", "")[:2500],
            ]
        )

        base_score = get_fused_base_score(row) * 100.0

        lexical_score = score_text_for_query(
            searchable_text,
            original_query,
            retrieval_query,
            intent,
        )

        intent_boost = document_intent_boost(
            document,
            original_query,
            intent,
        )

        snippet = select_relevant_snippet(
            document,
            original_query,
            retrieval_query,
            intent,
        )

        new_row = row.to_dict()
        new_row["rag_rerank_score"] = (
            base_score
            + lexical_score
            + intent_boost
        )
        new_row["rag_intent"] = intent
        new_row["title"] = document["title"]
        new_row["document_type"] = document["document_type"]
        new_row["course_code"] = document["course_code"]
        new_row["snippet"] = snippet

        reranked_rows.append(new_row)

    reranked = pd.DataFrame(reranked_rows)

    if reranked.empty:
        return fused_results.head(top_k).copy()

    reranked = reranked.sort_values(
        "rag_rerank_score",
        ascending=False,
    )

    selected_rows: list[pd.Series] = []
    source_counts: dict[str, int] = {}

    for _, row in reranked.iterrows():
        identity = source_identity(row)
        current_count = source_counts.get(identity, 0)

        if current_count >= max_chunks_per_source:
            continue

        selected_rows.append(row)
        source_counts[identity] = current_count + 1

        if len(selected_rows) >= top_k:
            break

    if not selected_rows:
        return pd.DataFrame()

    final_results = pd.DataFrame(selected_rows).reset_index(drop=True)
    final_results["rank"] = range(1, len(final_results) + 1)

    return final_results


def build_fact_line(
    rank: int,
    row: pd.Series,
) -> str:
    """Turn a reranked source into one LLM context fact."""

    descriptors: list[str] = []

    course_code = normalize_text(row.get("course_code"))
    title = normalize_text(row.get("title"))
    document_type = normalize_text(row.get("document_type"))
    snippet = normalize_text(row.get("snippet"))

    if course_code:
        descriptors.append(f"course {course_code}")

    if title:
        descriptors.append(f"titled {title}")

    if document_type:
        descriptors.append(f"source type {document_type}")

    descriptor = ", ".join(descriptors)

    if descriptor:
        return (
            f"Fact {rank}: In a department source for "
            f"{descriptor}, the relevant information says: {snippet}"
        )

    return f"Fact {rank}: {snippet}"


def build_hidden_rag_context(
    reranked_results: pd.DataFrame,
    max_total_chars: int | None = None,
) -> str:
    """Build size-limited factual context for the answer model."""

    limit = max_total_chars or settings.rag_max_context_chars
    fact_lines: list[str] = []
    total_chars = 0

    for _, row in reranked_results.iterrows():
        snippet = normalize_text(row.get("snippet"))

        if not snippet:
            continue

        rank = int(row.get("rank", len(fact_lines) + 1))
        fact_line = build_fact_line(rank, row)

        if (
            total_chars + len(fact_line) > limit
            and fact_lines
        ):
            break

        fact_lines.append(fact_line)
        total_chars += len(fact_line)

    return "\n".join(fact_lines)

def prioritize_exact_course_documents(
    results: pd.DataFrame,
    question: str,
) -> pd.DataFrame:
    """Move exact course-identity matches ahead of general documents."""

    if results.empty:
        return results.copy()

    requested_course_code = extract_course_code(question)

    if not requested_course_code:
        return results.copy()

    working = results.copy()

    exact_mask = (
        working.get(
            "course_code",
            pd.Series("", index=working.index),
        )
        .fillna("")
        .astype(str)
        .str.upper()
        .eq(requested_course_code)
    )

    if not exact_mask.any():
        return working

    exact_matches = working[exact_mask].copy()
    other_matches = working[~exact_mask].copy()

    prioritized = pd.concat(
        [
            exact_matches,
            other_matches,
        ],
        ignore_index=True,
    )

    prioritized["rank"] = range(
        1,
        len(prioritized) + 1,
    )

    return prioritized


def filter_low_confidence_documents(
    results: pd.DataFrame,
    minimum_ratio: float = 0.75,
    minimum_results: int = 2,
) -> pd.DataFrame:
    """Remove results that score far below the strongest document."""

    if results.empty:
        return results.copy()

    top_score = float(results.iloc[0]["rag_rerank_score"])
    threshold = top_score * minimum_ratio

    filtered = results[
        results["rag_rerank_score"] >= threshold
    ].copy()

    required_count = min(
        minimum_results,
        len(results),
    )

    if len(filtered) < required_count:
        filtered = results.head(required_count).copy()

    filtered = filtered.reset_index(drop=True)
    filtered["rank"] = range(1, len(filtered) + 1)

    return filtered

def retrieve_and_rerank(
    question: str,
    top_k: int = 5,
) -> RerankResult:
    """Run query expansion, hybrid retrieval, reranking, and context building."""

    original_query = normalize_text(question)

    if not original_query:
        raise ValueError("The retrieval question cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    retrieval_query = improve_query_for_hybrid_search(
        original_query
    )

    candidate_count = max(
        settings.rag_retrieval_pool,
        top_k,
    )

    fused_results = hybrid_search(
        question=retrieval_query,
        top_k=candidate_count,
        candidate_pool=candidate_count,
    )

    reranked_results = rerank_fused_results(
        fused_results=fused_results,
        original_query=original_query,
        retrieval_query=retrieval_query,
        top_k=top_k,
    )

    reranked_results = prioritize_exact_course_documents(
        reranked_results,
        original_query,
    )

    reranked_results = filter_low_confidence_documents(
        reranked_results
    )

    hidden_context = build_hidden_rag_context(
        reranked_results
    )

    return RerankResult(
        retrieval_query=retrieval_query,
        intent=classify_rag_intent(original_query),
        documents=reranked_results,
        hidden_context=hidden_context,
    )