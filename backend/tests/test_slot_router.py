import pytest

from app.conversation.session_store import (
    ConversationSession,
    reset_session_store,
)
from app.conversation.slot_router import (
    extract_slots_from_text,
    route_conversation_turn,
)


@pytest.fixture(autouse=True)
def _reset_sessions() -> None:
    reset_session_store()


def test_vague_degree_question_requests_program() -> None:
    decision = route_conversation_turn(
        question="What are my graduation requirements?",
        session=ConversationSession(),
    )

    assert decision.action == "clarify"
    assert decision.pending_slots == ["program"]
    assert "graduate program" in decision.clarification.lower()


def test_specific_degree_question_retrieves_immediately() -> None:
    decision = route_conversation_turn(
        question=(
            "What are the requirements for the "
            "MS in Computer Science?"
        ),
        session=ConversationSession(),
    )

    assert decision.action == "retrieve"
    assert "MS Computer Science" in decision.retrieval_query


def test_vague_schedule_question_requests_term() -> None:
    decision = route_conversation_turn(
        question="What graduate courses are available?",
        session=ConversationSession(),
    )

    assert decision.action == "clarify"
    assert decision.pending_slots == ["term"]
    assert "Fall 2025" in decision.clarification


def test_specific_schedule_question_retrieves_immediately() -> None:
    decision = route_conversation_turn(
        question="What courses are offered in Fall 2025?",
        session=ConversationSession(),
    )

    assert decision.action == "retrieve"
    assert "Fall 2025" in decision.retrieval_query
    assert "graduate course offerings schedule" in decision.retrieval_query


def test_follow_up_turn_completes_schedule_slots() -> None:
    first = route_conversation_turn(
        question="What classes are being offered?",
        session=ConversationSession(),
    )

    assert first.action == "clarify"
    assert first.updated_session is not None

    second = route_conversation_turn(
        question="Spring 2026",
        session=first.updated_session,
    )

    assert second.action == "retrieve"
    assert "Spring 2026" in second.retrieval_query


def test_course_code_question_skips_slot_filling() -> None:
    decision = route_conversation_turn(
        question="What are the prerequisites for CAP 4630?",
        session=ConversationSession(),
    )

    assert decision.action == "retrieve"
    assert decision.retrieval_query.startswith(
        "What are the prerequisites for CAP 4630?"
    )


def test_pending_program_reply_is_understood() -> None:
    session = ConversationSession(
        topic="degree_requirements",
        pending_slots=["program"],
    )

    slots = extract_slots_from_text(
        "Computer Science",
        pending_slots=["program"],
    )

    assert slots.program == "MS Computer Science"

    decision = route_conversation_turn(
        question="Computer Science",
        session=session,
    )

    assert decision.action == "retrieve"
    assert "MS Computer Science" in decision.retrieval_query


def test_vague_course_recommendation_requests_program() -> None:
    decision = route_conversation_turn(
        question="What courses should I take?",
        session=ConversationSession(),
    )

    assert decision.action == "clarify"
    assert decision.pending_slots == ["program"]


@pytest.mark.parametrize(
    ("label", "topic", "expected_phrase"),
    [
        ("Graduation", "graduation", "graduation"),
        ("Forms", "forms", "form"),
        ("Degree Requirements", "degree_requirements", "degree requirements"),
        ("Academic Calendar", "academic_calendar", "academic calendar"),
        ("Contact Advisor", "contact_advisor", "advis"),
    ],
)
def test_suggestion_buttons_ask_for_more_detail(
    label: str,
    topic: str,
    expected_phrase: str,
) -> None:
    decision = route_conversation_turn(
        question=label,
        session=ConversationSession(),
    )

    assert decision.action == "clarify"
    assert decision.topic == topic
    assert decision.pending_slots == ["detail"]
    assert expected_phrase in decision.clarification.lower()
    assert decision.updated_session is not None


def test_forms_button_follow_up_retrieves() -> None:
    first = route_conversation_turn(
        question="Forms",
        session=ConversationSession(),
    )

    assert first.action == "clarify"
    assert first.updated_session is not None

    second = route_conversation_turn(
        question="I need the plan of study form",
        session=first.updated_session,
    )

    assert second.action == "retrieve"
    assert "plan of study" in second.retrieval_query.lower()
    assert "graduate forms" in second.retrieval_query.lower()


def test_graduation_button_follow_up_retrieves() -> None:
    first = route_conversation_turn(
        question="Graduation",
        session=ConversationSession(),
    )

    second = route_conversation_turn(
        question="application deadlines",
        session=first.updated_session,
    )

    assert second.action == "retrieve"
    assert "application deadlines" in second.retrieval_query.lower()
    assert "graduation" in second.retrieval_query.lower()


def test_switching_suggestion_buttons_resets_topic() -> None:
    first = route_conversation_turn(
        question="Forms",
        session=ConversationSession(),
    )

    second = route_conversation_turn(
        question="Contact Advisor",
        session=first.updated_session,
    )

    assert second.action == "clarify"
    assert second.topic == "contact_advisor"
    assert second.pending_slots == ["detail"]
    assert "advis" in second.clarification.lower()


@pytest.mark.parametrize(
    ("keyword", "topic", "expected_phrase"),
    [
        ("Courses", "course_recommendation", "courses"),
        ("Credits", "degree_requirements", "degree requirements"),
        ("Prerequisites", "course_recommendation", "courses"),
        ("Schedule", "schedule_offerings", "term"),
        ("Certificate", "certificate_requirements", "certificate"),
        ("Advisor", "contact_advisor", "advis"),
        ("about courses", "course_recommendation", "courses"),
    ],
)
def test_short_keyword_questions_ask_for_more_detail(
    keyword: str,
    topic: str,
    expected_phrase: str,
) -> None:
    decision = route_conversation_turn(
        question=keyword,
        session=ConversationSession(),
    )

    assert decision.action == "clarify"
    assert decision.topic == topic
    assert decision.pending_slots == ["detail"]
    assert expected_phrase in decision.clarification.lower()


def test_courses_keyword_follow_up_retrieves() -> None:
    first = route_conversation_turn(
        question="Courses",
        session=ConversationSession(),
    )

    assert first.action == "clarify"
    assert first.updated_session is not None

    second = route_conversation_turn(
        question="What is offered in Fall 2025?",
        session=first.updated_session,
    )

    assert second.action == "retrieve"
    assert "Fall 2025" in second.retrieval_query


def test_short_follow_up_keyword_counts_as_detail() -> None:
    first = route_conversation_turn(
        question="Forms",
        session=ConversationSession(),
    )

    second = route_conversation_turn(
        question="application",
        session=first.updated_session,
    )

    assert second.action == "retrieve"
    assert "application" in second.retrieval_query.lower()
