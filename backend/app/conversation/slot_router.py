"""Rule-based slot filling and retrieval routing for advising chat."""

from dataclasses import dataclass
import re
from typing import Literal

from app.conversation.session_store import ConversationSession, SlotValues
from app.rag.generator import extract_course_codes, normalize_text


Topic = Literal[
    "degree_requirements",
    "schedule_offerings",
    "certificate_requirements",
    "course_recommendation",
]

RouteAction = Literal["clarify", "retrieve"]

MS_PROGRAMS = {
    "MS Computer Science",
    "MS Electrical Engineering",
    "MS Computer Engineering",
    "Professional MS Computer Science",
    "Professional MS AI",
    "Professional MS ITM",
    "PhD",
}

SCHEDULE_TERMS = [
    "schedule",
    "scheduled",
    "offering",
    "offerings",
    "offered",
    "available",
    "course listing",
    "course listings",
    "what courses are",
    "which courses are",
    "what classes are",
    "which classes are",
    "being offered",
    "this semester",
    "next semester",
    "course schedule",
]

DEGREE_TERMS = [
    "degree requirement",
    "degree requirements",
    "graduation requirement",
    "graduation requirements",
    "program requirement",
    "program requirements",
    "credit requirement",
    "credit requirements",
    "how many credits",
    "worksheet",
    "plan of study",
    "thesis option",
    "non-thesis",
    "non thesis",
    "thesis track",
]

RECOMMENDATION_TERMS = [
    "recommend",
    "should i take",
    "what should i take",
    "which courses should",
    "what courses should",
    "what classes should",
]

DIRECT_FORM_TERMS = [
    "worksheet",
    "plan of study",
    "application",
    "degree audit",
    "form",
]

DIRECT_PERSON_TERMS = [
    "advisor",
    "advise",
    "chair",
    "director",
    "coordinator",
    "dean",
]

CERTIFICATE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\b(?:artificial intelligence|(?<!\w)ai(?!\w))\s+certificate\b",
            flags=re.IGNORECASE,
        ),
        "Artificial Intelligence Certificate",
    ),
    (
        re.compile(
            r"\bbig data(?:\s+analytics)?\s+certificate\b",
            flags=re.IGNORECASE,
        ),
        "Big Data Analytics Certificate",
    ),
    (
        re.compile(
            r"\bcyber(?:\s+security|-security)?\s+certificate\b",
            flags=re.IGNORECASE,
        ),
        "Cybersecurity Certificate",
    ),
]

PROGRAM_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\bprofessional\s+(?:ms|master'?s?)\s*(?:in\s+)?ai\b",
            flags=re.IGNORECASE,
        ),
        "Professional MS AI",
    ),
    (
        re.compile(
            r"\bprofessional\s+(?:ms|master'?s?)\s*(?:in\s+)?"
            r"(?:cs|computer science)\b",
            flags=re.IGNORECASE,
        ),
        "Professional MS Computer Science",
    ),
    (
        re.compile(
            r"\bprofessional\s+(?:ms|master'?s?)\s*(?:in\s+)?itm\b",
            flags=re.IGNORECASE,
        ),
        "Professional MS ITM",
    ),
    (
        re.compile(
            r"\b(?:ms|m\.s\.|master'?s?)\s*(?:in\s+)?"
            r"(?:cs|cse|computer science)\b",
            flags=re.IGNORECASE,
        ),
        "MS Computer Science",
    ),
    (
        re.compile(
            r"\b(?:ms|m\.s\.|master'?s?)\s*(?:in\s+)?"
            r"(?:ee|electrical engineering)\b",
            flags=re.IGNORECASE,
        ),
        "MS Electrical Engineering",
    ),
    (
        re.compile(
            r"\b(?:ms|m\.s\.|master'?s?)\s*(?:in\s+)?"
            r"(?:computer engineering|cp?e)\b",
            flags=re.IGNORECASE,
        ),
        "MS Computer Engineering",
    ),
    (
        re.compile(
            r"\b(?:ph\.?d\.?|doctoral|doctorate)\b",
            flags=re.IGNORECASE,
        ),
        "PhD",
    ),
]

TERM_PATTERN = re.compile(
    r"\b(fall|spring|summer)\s*(20\d{2})\b",
    flags=re.IGNORECASE,
)

SEASON_ONLY_PATTERN = re.compile(
    r"\b(fall|spring|summer)\b",
    flags=re.IGNORECASE,
)

START_TERM_PATTERN = re.compile(
    r"\b(?:started|starting|began|beginning|start(?:ed)?\s+in)\s+"
    r"(fall|spring|summer)\s*(20\d{2})\b",
    flags=re.IGNORECASE,
)

RELATIVE_START_TERM_PATTERN = re.compile(
    r"\b(spring|fall|summer)\s*(20\d{2})\s+or\s+earlier\b",
    flags=re.IGNORECASE,
)

TRACK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\bnon[\s-]?thesis\b",
            flags=re.IGNORECASE,
        ),
        "non-thesis",
    ),
    (
        re.compile(
            r"\bthesis\s+(?:option|track|pathway|route)\b|\bthesis\b",
            flags=re.IGNORECASE,
        ),
        "thesis",
    ),
]

SLOT_LABELS = {
    "program": "graduate program",
    "track": "thesis or non-thesis option",
    "start_term": "program start term",
    "term": "academic term",
    "certificate": "certificate name",
}


@dataclass(frozen=True)
class RouteDecision:
    """Result of routing one conversation turn."""

    action: RouteAction
    retrieval_query: str
    clarification: str | None = None
    pending_slots: list[str] | None = None
    topic: str | None = None
    updated_session: ConversationSession | None = None


def route_conversation_turn(
    question: str,
    session: ConversationSession,
) -> RouteDecision:
    """Decide whether to clarify missing details or run retrieval."""

    normalized_question = normalize_text(question)

    if not normalized_question:
        raise ValueError("The conversation question cannot be empty.")

    extracted = extract_slots_from_text(
        normalized_question,
        pending_slots=session.pending_slots,
    )
    merged_slots = merge_slot_values(session.slots, extracted)

    if should_use_direct_retrieval(
        normalized_question,
        merged_slots,
    ):
        return RouteDecision(
            action="retrieve",
            retrieval_query=build_retrieval_query(
                normalized_question,
                merged_slots,
            ),
            updated_session=ConversationSession(),
        )

    topic = session.topic or detect_topic(
        normalized_question,
        merged_slots,
    )

    if topic is None:
        return RouteDecision(
            action="retrieve",
            retrieval_query=normalized_question,
            updated_session=ConversationSession(),
        )

    missing_slots = get_missing_slots(
        topic=topic,
        slots=merged_slots,
        question=normalized_question,
    )

    if missing_slots:
        updated_session = ConversationSession(
            topic=topic,
            slots=merged_slots,
            pending_slots=missing_slots,
        )

        return RouteDecision(
            action="clarify",
            retrieval_query="",
            clarification=build_clarification(
                topic=topic,
                missing_slots=missing_slots,
                slots=merged_slots,
            ),
            pending_slots=missing_slots,
            topic=topic,
            updated_session=updated_session,
        )

    return RouteDecision(
        action="retrieve",
        retrieval_query=build_retrieval_query(
            normalized_question,
            merged_slots,
            topic=topic,
        ),
        updated_session=ConversationSession(),
    )


def extract_slots_from_text(
    text: str,
    pending_slots: list[str] | None = None,
) -> SlotValues:
    """Extract known advising slots from one user message."""

    cleaned = normalize_text(text)

    if not cleaned:
        return SlotValues()

    pending = pending_slots or []

    program = extract_program(cleaned)
    track = extract_track(cleaned)
    start_term = extract_start_term(cleaned)
    term = extract_schedule_term(cleaned)
    certificate = extract_certificate(cleaned)

    if "start_term" in pending and not start_term:
        start_term = extract_schedule_term(cleaned) or extract_start_term(
            cleaned
        )

    if "term" in pending and not term:
        term = extract_schedule_term(cleaned)

    if "track" in pending and not track:
        track = extract_track(cleaned)

    if "program" in pending and not program:
        program = extract_program(cleaned) or infer_program_from_reply(
            cleaned
        )

    if "certificate" in pending and not certificate:
        certificate = extract_certificate(cleaned)

    return SlotValues(
        program=program,
        track=track,
        start_term=start_term,
        term=term,
        certificate=certificate,
    )


def merge_slot_values(
    existing: SlotValues,
    new_values: SlotValues,
) -> SlotValues:
    """Combine previously collected slots with newly extracted ones."""

    return SlotValues(
        program=new_values.program or existing.program,
        track=new_values.track or existing.track,
        start_term=new_values.start_term or existing.start_term,
        term=new_values.term or existing.term,
        certificate=new_values.certificate or existing.certificate,
    )


def should_use_direct_retrieval(
    question: str,
    slots: SlotValues,
) -> bool:
    """Return whether the question is specific enough to skip slot filling."""

    lowered = question.lower()
    course_codes = extract_course_codes(question)

    if course_codes:
        if is_schedule_question(lowered):
            if slots.term or extract_schedule_term(question):
                return True

            return False

        return True

    if slots.certificate or extract_certificate(question):
        return True

    if any(term in lowered for term in DIRECT_PERSON_TERMS):
        return True

    if any(term in lowered for term in DIRECT_FORM_TERMS):
        return True

    if slots.program and any(term in lowered for term in DEGREE_TERMS):
        return True

    if slots.program and "requirement" in lowered:
        return True

    if slots.term and is_schedule_question(lowered):
        return True

    if slots.program and any(
        term in lowered for term in RECOMMENDATION_TERMS
    ):
        return True

    return False


def detect_topic(
    question: str,
    slots: SlotValues,
) -> Topic | None:
    """Detect which advising topic needs slot filling."""

    lowered = question.lower()

    if is_schedule_question(lowered):
        return "schedule_offerings"

    if "certificate" in lowered or "certification" in lowered:
        return "certificate_requirements"

    if any(term in lowered for term in DEGREE_TERMS):
        return "degree_requirements"

    if any(term in lowered for term in RECOMMENDATION_TERMS):
        return "course_recommendation"

    if any(term in lowered for term in ["graduate", "grad ", "master", "phd"]):
        if any(
            term in lowered
            for term in [
                "requirement",
                "requirements",
                "credit",
                "credits",
                "graduate",
            ]
        ):
            return "degree_requirements"

    if SEASON_ONLY_PATTERN.search(lowered) and any(
        term in lowered
        for term in ["course", "courses", "class", "classes"]
    ):
        return "schedule_offerings"

    return None


def is_schedule_question(lowered_question: str) -> bool:
    """Return whether the user is asking about term schedules or offerings."""

    return any(
        term in lowered_question
        for term in SCHEDULE_TERMS
    )


def get_missing_slots(
    topic: Topic,
    slots: SlotValues,
    question: str,
) -> list[str]:
    """Return slot names still required before retrieval."""

    missing: list[str] = []

    if topic == "degree_requirements":
        if not slots.program:
            missing.append("program")

    elif topic == "schedule_offerings":
        course_codes = extract_course_codes(question)

        if not slots.term and not extract_schedule_term(question):
            if not course_codes:
                missing.append("term")

    elif topic == "certificate_requirements":
        if not slots.certificate and not extract_certificate(question):
            missing.append("certificate")

    elif topic == "course_recommendation":
        if not slots.program:
            missing.append("program")

    return missing


def build_clarification(
    topic: Topic,
    missing_slots: list[str],
    slots: SlotValues,
) -> str:
    """Build a user-facing follow-up question for missing slots."""

    next_slot = missing_slots[0]

    if topic == "degree_requirements":
        if next_slot == "program":
            return (
                "Which FAU EECS graduate program are you asking about? "
                "For example: MS in Computer Science, MS in Electrical "
                "Engineering, PhD, or a graduate certificate."
            )

    if topic == "schedule_offerings":
        if next_slot == "term":
            return (
                "Which term are you asking about? Please include the season "
                "and year, such as Fall 2025 or Spring 2026."
            )

    if topic == "certificate_requirements":
        if next_slot == "certificate":
            return (
                "Which graduate certificate are you asking about? For "
                "example: Artificial Intelligence, Big Data Analytics, or "
                "Cybersecurity."
            )

    if topic == "course_recommendation":
        if next_slot == "program":
            return (
                "Which FAU EECS graduate program should I use when "
                "recommending courses?"
            )

    return (
        "Could you share a bit more detail so I can look up the right "
        "FAU EECS information?"
    )


def build_retrieval_query(
    question: str,
    slots: SlotValues,
    topic: str | None = None,
) -> str:
    """Build a retrieval query from the question and collected slots."""

    parts = [question]

    if slots.program:
        parts.append(slots.program)

    if slots.track:
        parts.append(f"{slots.track} option")

    if slots.start_term:
        parts.append(f"start term {slots.start_term}")

    if slots.term:
        parts.append(f"{slots.term} term")

    if slots.certificate:
        parts.append(slots.certificate)

    if topic == "schedule_offerings":
        parts.append("graduate course offerings schedule")

    if topic == "course_recommendation":
        parts.append("graduate course recommendations")

    deduped: list[str] = []

    for part in parts:
        cleaned_part = normalize_text(part)

        if cleaned_part and cleaned_part not in deduped:
            deduped.append(cleaned_part)

    return " ".join(deduped)


def extract_program(text: str) -> str | None:
    """Extract a normalized graduate program name."""

    for pattern, label in PROGRAM_PATTERNS:
        if pattern.search(text):
            return label

    return None


def infer_program_from_reply(text: str) -> str | None:
    """Infer a program from short follow-up answers."""

    lowered = text.lower()

    if "computer science" in lowered or lowered in {"cs", "msc", "ms cs"}:
        return "MS Computer Science"

    if "electrical engineering" in lowered or lowered in {"ee", "ms ee"}:
        return "MS Electrical Engineering"

    if "computer engineering" in lowered or lowered in {"ce", "cpe"}:
        return "MS Computer Engineering"

    if "phd" in lowered or "doctoral" in lowered:
        return "PhD"

    return None


def extract_track(text: str) -> str | None:
    """Extract thesis or non-thesis track."""

    for pattern, label in TRACK_PATTERNS:
        if pattern.search(text):
            return label

    return None


def extract_start_term(text: str) -> str | None:
    """Extract a program start term."""

    relative_match = RELATIVE_START_TERM_PATTERN.search(text)

    if relative_match:
        season = relative_match.group(1).title()
        year = relative_match.group(2)

        return f"{season} {year} or earlier"

    start_match = START_TERM_PATTERN.search(text)

    if start_match:
        season = start_match.group(1).title()
        year = start_match.group(2)

        return f"{season} {year}"

    term_match = TERM_PATTERN.search(text)

    if term_match and any(
        marker in text.lower()
        for marker in (
            "started",
            "starting",
            "began",
            "beginning",
            "start term",
            "start in",
        )
    ):
        season = term_match.group(1).title()
        year = term_match.group(2)

        return f"{season} {year}"

    return None


def extract_schedule_term(text: str) -> str | None:
    """Extract a schedule term such as Fall 2025."""

    term_match = TERM_PATTERN.search(text)

    if term_match:
        season = term_match.group(1).title()
        year = term_match.group(2)

        return f"{season} {year}"

    return None


def extract_certificate(text: str) -> str | None:
    """Extract a normalized certificate name."""

    for pattern, label in CERTIFICATE_PATTERNS:
        if pattern.search(text):
            return label

    if re.search(
        r"\b(?:graduate\s+)?certificate\b",
        text,
        flags=re.IGNORECASE,
    ):
        lowered = text.lower()

        if "artificial intelligence" in lowered or re.search(
            r"\bai\b",
            lowered,
        ):
            return "Artificial Intelligence Certificate"

        if "big data" in lowered:
            return "Big Data Analytics Certificate"

        if "cyber" in lowered:
            return "Cybersecurity Certificate"

    return None
