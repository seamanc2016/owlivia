import pytest

from app.rag.generator import (
    OUT_OF_SCOPE_MESSAGE,
    build_contextualized_prompt,
    build_messages,
    is_in_scope_graduate_advising_question,
)


@pytest.mark.parametrize(
    "question",
    [
        "What are the requirements for the MS in Computer Science?",
        "What are the prerequisites for CAP 4630?",
        "Where can I find the plan of study form?",
        "How do I apply to the graduate program?",
        "What courses are in the Big Data Analytics certificate?",
    ],
)
def test_in_scope_graduate_advising_questions(
    question: str,
) -> None:
    assert is_in_scope_graduate_advising_question(question)


@pytest.mark.parametrize(
    "question",
    [
        "What's the weather in Boca Raton?",
        "Who won the Super Bowl last year?",
        "Write me Python code to sort a list",
        "How do I apply to MIT for computer science?",
        "Tell me a joke",
        "Hello",
    ],
)
def test_out_of_scope_questions(question: str) -> None:
    assert not is_in_scope_graduate_advising_question(question)


def test_prompt_includes_scope_rules() -> None:
    prompt = build_contextualized_prompt(
        question="What are the MS requirements?",
        hidden_context="Fact 1: Example fact.",
    )

    assert "Scope rules:" in prompt
    assert OUT_OF_SCOPE_MESSAGE in prompt
    assert "Strict rules:" in prompt


def test_system_message_limits_to_graduate_advising() -> None:
    messages = build_messages(
        question="What are the MS requirements?",
        hidden_context="Fact 1: Example fact.",
    )

    system_message = messages[0]["content"]

    assert "graduate academic advising assistant" in system_message
    assert "only answer questions about FAU EECS graduate" in system_message
