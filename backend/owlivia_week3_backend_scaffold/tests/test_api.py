from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer week3-prototype-token"}


def test_health_check_reports_backend_online() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["services"]["backend"] == "online"


def test_valid_chat_question_returns_integration_contract() -> None:
    response = client.post(
        "/api/chat",
        headers=AUTH_HEADERS,
        json={"question": "  What are the graduate credit requirements?  ", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    UUID(body["response_id"])
    UUID(body["session_id"])
    assert body["retrieval_mode"] == "connected"
    assert len(body["sources"]) > 0


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
    response = client.post("/api/chat", json={"question": "How do I apply?"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_auth_rejects_wrong_header_scheme() -> None:
    response = client.get(
        "/api/auth/verify",
        headers={"Authorization": "Basic not-a-bearer-token"},
    )

    assert response.status_code == 401


def test_valid_feedback_is_accepted() -> None:
    chat_response = client.post(
        "/api/chat",
        headers=AUTH_HEADERS,
        json={"question": "Where can I find advising forms?"},
    )
    response_id = chat_response.json()["response_id"]

    response = client.post(
        "/api/feedback",
        headers=AUTH_HEADERS,
        json={"response_id": response_id, "rating": 5, "comment": " Helpful. "},
    )

    assert response.status_code == 201
    assert response.json()["response_id"] == response_id
    assert response.json()["received"] is True


def test_feedback_rejects_rating_outside_scale() -> None:
    response = client.post(
        "/api/feedback",
        headers=AUTH_HEADERS,
        json={"response_id": "d7cc9cb4-bf5e-4c1a-8fc7-15d43ef4e768", "rating": 6},
    )

    assert response.status_code == 422

