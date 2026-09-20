"""Tests for the optional production workshop-login barrier."""

from fastapi.testclient import TestClient

from app.api.v1.routes import auth as auth_route
from app.core.auth import create_password_hash
from app.core.config import Settings
from app.main import create_app
import app.main as main_module


def test_protected_api_requires_and_accepts_a_signed_login(monkeypatch) -> None:
    configuration = Settings(
        app_auth_enabled=True,
        app_auth_username="werkstatt",
        app_auth_password_hash=create_password_hash("correct horse battery staple"),
        app_auth_session_secret="a" * 48,
    )
    monkeypatch.setattr(main_module, "settings", configuration)
    monkeypatch.setattr(auth_route, "settings", configuration)
    client = TestClient(create_app(), base_url="https://testserver")

    assert client.post("/api/v1/registrations/validate", json={}).status_code == 401
    assert client.post(
        "/api/v1/auth/login",
        json={"username": "werkstatt", "password": "wrong"},
    ).status_code == 401

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "werkstatt", "password": "correct horse battery staple"},
    )
    assert login.status_code == 200
    assert "HttpOnly" in login.headers["set-cookie"]
    assert "Secure" in login.headers["set-cookie"]
    assert client.post("/api/v1/registrations/validate", json={}).status_code == 200
