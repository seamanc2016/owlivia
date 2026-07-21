from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes import chat as chat_route
from app.services import retrieve_advising_context


client = TestClient(app)

AUTH_HEADERS = {
    "Authorization": "Bearer week3-prototype-token",
}


def test_health_check_reports_backend_online() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["services"]["backend"] == "online"


def test_valid_chat_question_returns_connected_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the API contract without loading Qwen during pytest."""

    monkeypatch.setattr(
        chat_route,
        "generate_answer",
        lambda question, retrieval: (
            "Grounded test answer from retrieved FAU EECS sources."
        ),
    )

    response = client.post(
        "/api/chat",
        headers=AUTH_HEADERS,
        json={
            "question": (
                "What are the requirements for the "
                "MS in Computer Science?"
            ),
            "top_k": 5,
        },
    )

    assert response.status_code == 200

    body = response.json()

    UUID(body["response_id"])
    UUID(body["session_id"])

    assert body["answer"] == (
        "Grounded test answer from retrieved FAU EECS sources."
    )
    assert body["retrieval_mode"] == "connected"
    assert body["confidence_status"] in {
        "low",
        "medium",
        "high",
    }
    assert body["sources"]

    assert all(
        source["document_id"] != "prototype-source-001"
        for source in body["sources"]
    )

    assert body["escalation_recommended"] == (
        body["confidence_status"] == "low"
    )


@pytest.mark.parametrize(
    ("question", "expected_phrase"),
    [
        (
            "What are the requirements for the "
            "MS in Computer Science?",
            "computer science",
        ),
        (
            "Where can I find the Artificial Intelligence "
            "certificate worksheet?",
            "artificial intelligence",
        ),
        (
            "What courses are included in the "
            "Big Data Analytics certificate?",
            "big data",
        ),
        (
            "What are the prerequisites for CAP 4630?",
            "cap 4630",
        ),
    ],
)
def test_real_retrieval_returns_relevant_sources(
    question: str,
    expected_phrase: str,
) -> None:
    """Run real LanceDB retrieval without loading the Qwen generator."""

    retrieval = retrieve_advising_context(
        question=question,
        top_k=5,
    )

    assert retrieval.mode == "connected"
    assert retrieval.sources
    assert retrieval.context_chunks
    assert retrieval.confidence_status in {
        "low",
        "medium",
        "high",
    }

    assert all(
        source.document_id != "prototype-source-001"
        for source in retrieval.sources
    )

    source_parts: list[str] = []

    for source in retrieval.sources:
        source_parts.extend(
            [
                source.title,
                source.url or "",
                source.category or "",
                source.excerpt or "",
            ]
        )

    searchable_text = " ".join(
        [
            *source_parts,
            *retrieval.context_chunks,
        ]
    ).lower()

    assert expected_phrase in searchable_text


def test_chat_rejects_whitespace_question() -> None:
    response = client.post(
        "/api/chat",
        headers=AUTH_HEADERS,
        json={"question": "   "},
    )

    assert response.status_code == 422


def test_chat_rejects_question_over_limit() -> None:
    response = client.post(
        "/api/chat",
        headers=AUTH_HEADERS,
        json={"question": "a" * 2001},
    )

    assert response.status_code == 422


def test_chat_requires_bearer_token() -> None:
    response = client.post(
        "/api/chat",
        json={"question": "How do I apply?"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_auth_rejects_wrong_header_scheme() -> None:
    response = client.get(
        "/api/auth/verify",
        headers={
            "Authorization": "Basic not-a-bearer-token",
        },
    )

    assert response.status_code == 401


def test_valid_feedback_is_accepted() -> None:
    response_id = str(uuid4())

    response = client.post(
        "/api/feedback",
        headers=AUTH_HEADERS,
        json={
            "response_id": response_id,
            "rating": 5,
            "comment": " Helpful. ",
        },
    )

    assert response.status_code == 201
    assert response.json()["response_id"] == response_id
    assert response.json()["received"] is True


def test_feedback_rejects_rating_outside_scale() -> None:
    response = client.post(
        "/api/feedback",
        headers=AUTH_HEADERS,
        json={
            "response_id": (
                "d7cc9cb4-bf5e-4c1a-8fc7-15d43ef4e768"
            ),
            "rating": 6,
        },
    )

    assert response.status_code == 422