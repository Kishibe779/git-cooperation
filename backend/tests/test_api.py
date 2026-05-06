from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def test_healthcheck() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_meta_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/meta")
    assert response.status_code == 200
    data = response.json()
    assert "default_provider" in data
    assert "mock" not in data["available_providers"]


def test_frontend_index_is_served_from_root() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "CareerPilot" in response.text


def test_frontend_deep_link_falls_back_to_index() -> None:
    client = TestClient(app)
    response = client.get("/plans")
    assert response.status_code == 200
    assert "CareerPilot" in response.text


def test_frontend_asset_is_served() -> None:
    client = TestClient(app)
    response = client.get("/app.js")
    assert response.status_code == 200
    assert "renderRoute" in response.text


def test_analyze_endpoint() -> None:
    client = TestClient(app)
    payload = {
        "candidate_name": "Demo User",
        "target_role": "Backend Engineer",
        "resume_text": "Used Python, Flask, SQL, and documentation to build internal tools and improve efficiency by 20 percent.",
        "job_description": "The role requires Python, data analysis, communication, documentation, and result-oriented delivery.",
        "provider": "mock",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["candidate_name"] == "Demo User"
    assert data["provider_meta"]["provider_used"] == "mock"
    assert "summary" in data
    assert "match_overview" in data


def test_deepseek_strict_does_not_fallback_without_key(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    get_settings.cache_clear()
    client = TestClient(app)
    payload = {
        "candidate_name": "Strict Demo",
        "target_role": "AI Product Assistant",
        "resume_text": "Used Python and FastAPI to build an AI resume product with documentation and delivery metrics.",
        "job_description": "The role requires Python, AI application experience, documentation, communication, and delivery.",
        "provider": "deepseek_strict",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 503
    assert response.json()["error"] == "provider_configuration_error"
    get_settings.cache_clear()


def test_auth_plans_and_history_flow() -> None:
    client = TestClient(app)
    email = "course-demo@example.com"
    register_response = client.post(
        "/api/v1/auth/register",
        json={"name": "Course User", "email": email, "password": "password123"},
    )
    if register_response.status_code == 409:
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "password123"},
        )
        assert login_response.status_code == 200
        auth_data = login_response.json()
    else:
        assert register_response.status_code == 200
        auth_data = register_response.json()

    token = auth_data["token"]
    headers = {"Authorization": f"Bearer {token}"}
    plans_response = client.get("/api/v1/plans")
    assert plans_response.status_code == 200
    assert any(plan["id"] == "pro" for plan in plans_response.json())

    checkout_response = client.post("/api/v1/billing/checkout", json={"plan": "pro"}, headers=headers)
    assert checkout_response.status_code == 200
    assert checkout_response.json()["plan"] == "pro"

    payload = {
        "candidate_name": "History User",
        "target_role": "AI Product Manager",
        "resume_text": "Used Python and DeepSeek tools to build an AI prototype, write docs, analyze requirements, and coordinate delivery.",
        "job_description": "The role needs AI application, large model tools, requirement analysis, project management, and communication.",
        "provider": "mock",
    }
    analyze_response = client.post("/api/v1/analyze", json=payload, headers=headers)
    assert analyze_response.status_code == 200
    assert analyze_response.json()["id"]

    history_response = client.get("/api/v1/analyses", headers=headers)
    assert history_response.status_code == 200
    assert len(history_response.json()["items"]) >= 1

    logout_response = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == 200
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 401


def test_register_validation_rejects_weak_password() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Weak User", "email": "weak@example.com", "password": "password"},
    )
    assert response.status_code == 422
