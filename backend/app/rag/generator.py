"""Grounded Qwen answer generation for the Owlivia advising assistant."""

from dataclasses import dataclass
from functools import lru_cache
from typing import Any
import re

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.config import settings


INSUFFICIENT_INFORMATION_MESSAGE = (
    "The retrieved department documents do not provide enough "
    "information to answer that."
)


COURSE_CODE_PATTERN = re.compile(
    r"\b(CAP|CDA|CEN|CGS|CIS|CNT|COP|COT|EEE|EEL|EGN)"
    r"\s*[-_ ]?\s*(\d{4}[A-Z]?)\b",
    flags=re.IGNORECASE,
)


SENSITIVE_ACADEMIC_CLAIMS = [
    "dissertation",
    "doctoral dissertation",
    "comprehensive exam",
    "qualifying exam",
    "internship requirement",
    "required internship",
    "capstone requirement",
    "required capstone",
    "research methods",
    "project work",
    "oral defense",
    "thesis defense",
]


@dataclass(frozen=True)
class GeneratedAnswer:
    """Final generator output and whether a fallback was required."""

    answer: str
    used_fallback: bool
    model_name: str


def normalize_text(value: Any) -> str:
    """Normalize whitespace and remove null-like values."""

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    cleaned = " ".join(
        str(value).replace("\x00", " ").split()
    )

    if cleaned.lower() in {
        "nan",
        "none",
        "null",
    }:
        return ""

    return cleaned


def normalize_multiline_text(value: Any) -> str:
    """Normalize text while preserving meaningful line breaks."""

    if value is None:
        return ""

    lines = [
        normalize_text(line)
        for line in str(value).splitlines()
    ]

    return "\n".join(
        line
        for line in lines
        if line
    )


def extract_course_codes(text: str) -> set[str]:
    """Extract and normalize EECS course codes from text."""

    return {
        f"{match.group(1).upper()} {match.group(2).upper()}"
        for match in COURSE_CODE_PATTERN.finditer(str(text))
    }


def first_course_code(text: str) -> str:
    """Return the first normalized EECS course code in text."""

    match = COURSE_CODE_PATTERN.search(str(text))

    if not match:
        return ""

    return f"{match.group(1).upper()} {match.group(2).upper()}"


@lru_cache(maxsize=1)
def get_tokenizer() -> Any:
    """Load and cache the Qwen tokenizer."""

    tokenizer = AutoTokenizer.from_pretrained(
        settings.rag_model_name
    )

    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    return tokenizer


@lru_cache(maxsize=1)
def get_model() -> Any:
    """Load and cache Qwen once per backend process."""

    model_kwargs: dict[str, Any] = {
        "low_cpu_mem_usage": True,
    }

    if torch.cuda.is_available():
        model_kwargs.update(
            {
                "dtype": torch.float16,
                "device_map": "auto",
            }
        )
    else:
        model_kwargs["dtype"] = torch.float32

    model = AutoModelForCausalLM.from_pretrained(
        settings.rag_model_name,
        **model_kwargs,
    )

    if not torch.cuda.is_available():
        model.to("cpu")

    model.eval()

    return model


def get_model_device(model: Any) -> torch.device:
    """Return the device holding the model's input parameters."""

    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )


def get_generator_summary() -> dict[str, Any]:
    """Return model information for local verification."""

    model = get_model()
    device = get_model_device(model)

    try:
        dtype = str(next(model.parameters()).dtype)
    except StopIteration:
        dtype = "unknown"

    return {
        "model_name": settings.rag_model_name,
        "device": str(device),
        "dtype": dtype,
        "cuda_available": torch.cuda.is_available(),
    }


def build_contextualized_prompt(
    question: str,
    hidden_context: str,
) -> str:
    """Build a strictly grounded advising prompt for Qwen."""

    question_text = normalize_text(question)
    context_text = normalize_multiline_text(hidden_context)

    return f"""
Answer the student's question using only the department facts below.

Strict rules:
- Only state requirements explicitly contained in the department facts.
- Preserve course codes exactly as written in the department facts.
- Every number in the answer must appear in the department facts.
- Do not calculate, combine, infer, or guess credit totals.
- Do not invent courses, exams, research requirements, dissertations,
  projects, internships, deadlines, forms, or academic policies.
- Do not replace "thesis" with "dissertation."
- Clearly distinguish between requirements that apply to different
  student start terms.
- When the facts contain only part of a requirement, state only that part.
- Keep the answer direct, clear, and concise.
- Do not mention fact numbers, filenames, document IDs, chunks, hidden
  context, vector search, BM25, LanceDB, RRF, or retrieval.

When the facts do not contain enough information, respond exactly with:
"{INSUFFICIENT_INFORMATION_MESSAGE}"

Student question:
{question_text}

Department facts:
{context_text}

Answer:
""".strip()


def build_messages(
    question: str,
    hidden_context: str,
) -> list[dict[str, str]]:
    """Build the messages used by Qwen's chat template."""

    system_message = (
        "You are Owlivia, an academic advising assistant for Florida "
        "Atlantic University's Electrical Engineering and Computer "
        "Science department. Use only the supplied department facts. "
        "Never invent academic requirements, course codes, or perform "
        "unsupported credit calculations. If the evidence is incomplete, "
        "state that the department documents do not provide enough information."
    )

    user_message = build_contextualized_prompt(
        question=question,
        hidden_context=hidden_context,
    )

    return [
        {
            "role": "system",
            "content": system_message,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]


def clean_generated_answer(answer: str) -> str:
    """Remove generation prefixes and normalize the answer."""

    cleaned = normalize_text(answer)

    cleaned = re.sub(
        r"^(Answer:|Final answer:|Final answer for the user:)\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    return cleaned


def repeated_word_problem(answer: str) -> bool:
    """Detect severely repetitive model output."""

    words = re.findall(
        r"[A-Za-z]+",
        normalize_text(answer).lower(),
    )

    if len(words) < 20:
        return False

    counts = {
        word: words.count(word)
        for word in set(words)
    }

    highest_count = max(
        counts.values(),
        default=0,
    )

    return highest_count / len(words) > 0.22


def answer_looks_bad(answer: str) -> bool:
    """Detect empty, repetitive, or retrieval-leaking output."""

    cleaned = normalize_text(answer)

    if len(cleaned) < 12:
        return True

    lowered = cleaned.lower()

    forbidden_markers = [
        "doc id",
        "document 1",
        "document 2",
        "document 3",
        "fact 1",
        "fact 2",
        "fact 3",
        "rrf",
        "bm25",
        "lancedb",
        "vector search",
        "retrieved chunk",
        "hidden context",
        "file_name",
        "source_page",
    ]

    if any(
        marker in lowered
        for marker in forbidden_markers
    ):
        return True

    if repeated_word_problem(cleaned):
        return True

    if re.fullmatch(
        r"[A-Za-z0-9_\- .()]+\.pdf",
        cleaned,
    ):
        return True

    return False


def extract_claim_numbers(text: str) -> set[str]:
    """Extract numeric claims while ignoring list-number markers."""

    cleaned = str(text)

    cleaned = re.sub(
        r"(?m)^\s*\d+[.)]\s*",
        "",
        cleaned,
    )

    numbers = re.findall(
        r"\b\d[\d,]*(?:\.\d+)?\b",
        cleaned,
    )

    return {
        number.replace(",", "")
        for number in numbers
    }


def answer_is_grounded(
    answer: str,
    hidden_context: str,
) -> bool:
    """Reject numeric, course-code, or academic claims absent from evidence."""

    cleaned_answer = normalize_text(answer)
    cleaned_context = normalize_text(hidden_context)

    answer_numbers = extract_claim_numbers(cleaned_answer)
    context_numbers = extract_claim_numbers(cleaned_context)

    unsupported_numbers = answer_numbers - context_numbers

    if unsupported_numbers:
        return False

    answer_course_codes = extract_course_codes(cleaned_answer)
    context_course_codes = extract_course_codes(cleaned_context)

    unsupported_course_codes = (
        answer_course_codes
        - context_course_codes
    )

    if unsupported_course_codes:
        return False

    answer_lower = cleaned_answer.lower()
    context_lower = cleaned_context.lower()

    for claim in SENSITIVE_ACADEMIC_CLAIMS:
        if (
            claim in answer_lower
            and claim not in context_lower
        ):
            return False

    return True


def _prepare_model_inputs(
    question: str,
    hidden_context: str,
    max_input_tokens: int,
) -> dict[str, torch.Tensor]:
    """Format and tokenize the prompt using Qwen's chat template."""

    tokenizer = get_tokenizer()
    model = get_model()

    messages = build_messages(
        question=question,
        hidden_context=hidden_context,
    )

    formatted_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(
        formatted_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_input_tokens,
    )

    device = get_model_device(model)

    return {
        key: value.to(device)
        for key, value in inputs.items()
    }


def run_model_once(
    question: str,
    hidden_context: str,
    max_input_tokens: int,
    max_new_tokens: int,
) -> str:
    """Generate one deterministic answer using Qwen."""

    tokenizer = get_tokenizer()
    model = get_model()

    inputs = _prepare_model_inputs(
        question=question,
        hidden_context=hidden_context,
        max_input_tokens=max_input_tokens,
    )

    input_length = inputs["input_ids"].shape[-1]

    generation_kwargs: dict[str, Any] = {
        "max_new_tokens": max_new_tokens,
        "do_sample": False,
        "no_repeat_ngram_size": 3,
        "repetition_penalty": 1.15,
        "pad_token_id": tokenizer.pad_token_id,
        "use_cache": True,
    }

    if tokenizer.eos_token_id is not None:
        generation_kwargs["eos_token_id"] = (
            tokenizer.eos_token_id
        )

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            **generation_kwargs,
        )

    generated_tokens = outputs[0][input_length:]

    answer = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True,
    )

    return clean_generated_answer(answer)


def _prerequisite_fallback_answer(
    question: str,
    records: list[tuple[str, str]],
) -> str:
    """Extract a course prerequisite directly from retrieved evidence."""

    requested_code = first_course_code(question)

    if not requested_code:
        return ""

    requested_compact = requested_code.replace(" ", "").lower()

    for title, snippet in records:
        identity_text = f"{title} {snippet}".lower()
        identity_compact = re.sub(
            r"[^a-z0-9]",
            "",
            identity_text,
        )

        if requested_compact not in identity_compact:
            continue

        prerequisite_match = re.search(
            r"\bprerequisites?\s*:\s*(.{1,180})",
            snippet,
            flags=re.IGNORECASE,
        )

        if not prerequisite_match:
            continue

        prerequisite_text = prerequisite_match.group(1)

        prerequisite_text = re.split(
            r"\s+(?:catalog description|specific course information)\b",
            prerequisite_text,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]

        prerequisite_text = re.sub(
            r"\s+[a-z]\.\s*$",
            "",
            prerequisite_text,
            flags=re.IGNORECASE,
        )

        prerequisite_codes = [
            code
            for code in extract_course_codes(prerequisite_text)
            if code != requested_code
        ]

        if not prerequisite_codes:
            continue

        unique_codes = list(dict.fromkeys(prerequisite_codes))

        if len(unique_codes) == 1:
            return (
                f"The prerequisite for {requested_code} "
                f"is {unique_codes[0]}."
            )

        return (
            f"The prerequisites for {requested_code} are "
            + ", ".join(unique_codes[:-1])
            + f", and {unique_codes[-1]}."
        )

    return ""


def extractive_fallback_answer(
    question: str,
    documents: pd.DataFrame | None,
) -> str:
    """Build a concise, grounded answer from retrieved document facts."""

    if documents is None or documents.empty:
        return INSUFFICIENT_INFORMATION_MESSAGE

    records: list[tuple[str, str]] = []

    for _, row in documents.head(5).iterrows():
        title = normalize_text(row.get("title"))
        snippet = normalize_text(row.get("snippet"))

        if snippet:
            records.append((title, snippet))

    if not records:
        return INSUFFICIENT_INFORMATION_MESSAGE

    prerequisite_answer = _prerequisite_fallback_answer(
        question=question,
        records=records,
    )

    if prerequisite_answer:
        return prerequisite_answer

    combined_text = " ".join(
        snippet
        for _, snippet in records
    )

    facts: list[str] = []

    total_match = re.search(
        r"\(?\b(\d+)\s+credit hours total\b\)?",
        combined_text,
        flags=re.IGNORECASE,
    )

    if total_match:
        facts.append(
            "The MS in Computer Science program worksheet lists "
            f"{total_match.group(1)} credit hours total."
        )

    if re.search(
        r"thesis\s+and\s+non-thesis\s+options",
        combined_text,
        flags=re.IGNORECASE,
    ):
        facts.append(
            "Students may choose between thesis and non-thesis options."
        )

    pos_match = re.search(
        r"after completing\s+(\d+)\s+credit hours"
        r".{0,250}?"
        r"submit their program worksheet and plan of study\s*\(pos\)",
        combined_text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if pos_match:
        facts.append(
            f"After completing {pos_match.group(1)} credit hours of "
            "coursework, students must submit their program worksheet "
            "and Plan of Study (POS) to the EECS Department."
        )

    for title, snippet in records:
        if "spring 2025 or earlier" not in title.lower():
            continue

        elective_match = re.search(
            r"students must complete\s+(\d+)\s+elective courses"
            r"\s*\(\s*(\d+)\s*(?:crs|credits?|credit hours)\s*\)",
            snippet,
            flags=re.IGNORECASE,
        )

        if elective_match:
            facts.append(
                "For students who started in Spring 2025 or earlier, "
                "the retrieved non-thesis requirements state that "
                f"students must complete {elective_match.group(1)} "
                "graduate elective courses totaling "
                f"{elective_match.group(2)} credits "
                "from courses offered by the EECS Department."
            )

        break

    if not facts:
        return INSUFFICIENT_INFORMATION_MESSAGE

    introduction = (
        "Based on the retrieved FAU EECS program worksheets:"
    )

    formatted_facts = "\n".join(
        f"- {fact}"
        for fact in facts
    )

    return f"{introduction}\n{formatted_facts}"


def generate_rag_answer(
    question: str,
    hidden_context: str,
    documents: pd.DataFrame | None = None,
    max_input_tokens: int | None = None,
    max_new_tokens: int | None = None,
) -> GeneratedAnswer:
    """Generate a grounded answer with validation, retry, and fallback."""

    normalized_question = normalize_text(question)
    normalized_context = normalize_multiline_text(hidden_context)

    if not normalized_question:
        raise ValueError(
            "The generation question cannot be empty."
        )

    if not normalized_context:
        return GeneratedAnswer(
            answer=INSUFFICIENT_INFORMATION_MESSAGE,
            used_fallback=True,
            model_name=settings.rag_model_name,
        )

    input_limit = (
        max_input_tokens
        if max_input_tokens is not None
        else settings.rag_max_input_tokens
    )

    output_limit = (
        max_new_tokens
        if max_new_tokens is not None
        else settings.rag_max_new_tokens
    )

    try:
        answer = run_model_once(
            question=normalized_question,
            hidden_context=normalized_context,
            max_input_tokens=input_limit,
            max_new_tokens=output_limit,
        )
    except Exception:
        fallback = extractive_fallback_answer(
            question=normalized_question,
            documents=documents,
        )

        return GeneratedAnswer(
            answer=fallback,
            used_fallback=True,
            model_name=settings.rag_model_name,
        )

    if (
        not answer_looks_bad(answer)
        and answer_is_grounded(
            answer,
            normalized_context,
        )
    ):
        return GeneratedAnswer(
            answer=answer,
            used_fallback=False,
            model_name=settings.rag_model_name,
        )

    shorter_context = "\n".join(
        normalized_context.splitlines()[:3]
    )

    try:
        retry_answer = run_model_once(
            question=normalized_question,
            hidden_context=shorter_context,
            max_input_tokens=min(input_limit, 1024),
            max_new_tokens=min(output_limit, 160),
        )
    except Exception:
        retry_answer = ""

    if (
        retry_answer
        and not answer_looks_bad(retry_answer)
        and answer_is_grounded(
            retry_answer,
            shorter_context,
        )
    ):
        return GeneratedAnswer(
            answer=retry_answer,
            used_fallback=False,
            model_name=settings.rag_model_name,
        )

    fallback = extractive_fallback_answer(
        question=normalized_question,
        documents=documents,
    )

    return GeneratedAnswer(
        answer=fallback,
        used_fallback=True,
        model_name=settings.rag_model_name,
    )


def _documents_from_context_chunks(
    context_chunks: list[str],
) -> pd.DataFrame:
    """Reconstruct minimal fallback records from internal fact lines."""

    records: list[dict[str, str]] = []

    for chunk in context_chunks:
        cleaned_chunk = normalize_text(chunk)

        if not cleaned_chunk:
            continue

        title_match = re.search(
            r"titled\s+(.+?)(?:,\s*source type|,\s*the relevant)",
            cleaned_chunk,
            flags=re.IGNORECASE,
        )

        snippet_match = re.search(
            r"the relevant information says:\s*(.+)$",
            cleaned_chunk,
            flags=re.IGNORECASE,
        )

        records.append(
            {
                "title": (
                    normalize_text(title_match.group(1))
                    if title_match
                    else ""
                ),
                "snippet": (
                    normalize_text(snippet_match.group(1))
                    if snippet_match
                    else cleaned_chunk
                ),
            }
        )

    return pd.DataFrame(records)


def generate(
    question: str,
    context_chunks: list[str],
) -> str:
    """Generate an answer from service-layer context chunks."""

    cleaned_chunks: list[str] = []

    for chunk in context_chunks:
        cleaned_chunk = normalize_text(chunk)

        if cleaned_chunk:
            cleaned_chunks.append(cleaned_chunk)

    hidden_context = "\n".join(cleaned_chunks)

    documents = _documents_from_context_chunks(
        cleaned_chunks
    )

    generated = generate_rag_answer(
        question=question,
        hidden_context=hidden_context,
        documents=documents,
    )

    return generated.answer