"""Tests for authentication middleware."""

import os
import pytest
from fastapi.testclient import TestClient
from src.trajgen.api import app
from src.trajgen.auth import LOGIN_URL, generate_session_token, verify_session_token


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def auth_enabled(monkeypatch):
    """Enable authentication for tests."""
    monkeypatch.setenv('APP_PASSWORD', 'test_password_123')
    yield
    monkeypatch.delenv('APP_PASSWORD', raising=False)


def _location(response) -> str:
    return response.headers.get('location', '')


def test_health_endpoint_public(client):
    """Health endpoint should be accessible without auth."""
    response = client.get("/api/health")
    # Should not be 401 (auth error), even if service is not initialized (503)
    assert response.status_code != 401


def test_public_paths_without_auth(client, auth_enabled):
    """Public paths should be accessible even when auth is enabled."""
    response = client.get("/api/health")
    assert response.status_code != 401

    response = client.get(LOGIN_URL)
    assert response.status_code == 200
    assert "NOTIONAL DEMO" in response.text
    assert "/api/login" in response.text


def test_login_alias_is_public(client, auth_enabled):
    """The /login alias should serve the same public login page."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "NOTIONAL DEMO" in response.text


def test_protected_api_requires_auth(client, auth_enabled):
    """Unauthenticated /api/* requests must return 401 JSON, not a redirect."""
    response = client.get("/api/config", follow_redirects=False)
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_unauthenticated_root_redirects_to_login(client, auth_enabled):
    """Unauthenticated / must redirect to the login URL, which returns 200."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert LOGIN_URL in _location(response)

    login_page = client.get(LOGIN_URL)
    assert login_page.status_code == 200
    assert "NOTIONAL DEMO" in login_page.text
    assert 'name="password"' in login_page.text


def test_unauthenticated_index_redirects_to_login(client, auth_enabled):
    """The main UI must not be reachable via /static/index.html without login."""
    response = client.get("/static/index.html", follow_redirects=False)
    assert response.status_code == 302
    assert LOGIN_URL in _location(response)


def test_unauthenticated_ui_assets_redirect_to_login(client, auth_enabled):
    """Main UI assets must not be public when auth is enabled."""
    for path in ("/static/app.js", "/static/style.css"):
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 302, f"{path} should redirect, got {response.status_code}"
        assert LOGIN_URL in _location(response)


def test_login_with_correct_password(client, auth_enabled):
    """Login should succeed with correct password and set the session cookie."""
    response = client.post("/api/login", data={"password": "test_password_123"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "session_token" in response.cookies


def test_login_with_incorrect_password(client, auth_enabled):
    """Login should fail with incorrect password."""
    response = client.post("/api/login", data={"password": "wrong_password"})
    assert response.status_code == 401


def test_login_grants_access_to_ui_and_api(client, auth_enabled):
    """After a successful login, index.html, app.js, and the API return 200."""
    login = client.post("/api/login", data={"password": "test_password_123"})
    assert login.status_code == 200
    assert "session_token" in login.cookies

    index = client.get("/static/index.html")
    assert index.status_code == 200
    assert "NOTIONAL DEMO" in index.text

    app_js = client.get("/static/app.js")
    assert app_js.status_code == 200

    style = client.get("/static/style.css")
    assert style.status_code == 200

    api = client.get("/api/config")
    assert api.status_code != 401


def test_session_token_grants_access(client, auth_enabled):
    """Valid session token should grant access to protected endpoints."""
    token = generate_session_token("test_password_123")

    response = client.get("/api/config", cookies={"session_token": token})
    assert response.status_code != 401


def test_invalid_session_token_denies_access(client, auth_enabled):
    """Invalid session token should not grant access."""
    response = client.get(
        "/api/config",
        cookies={"session_token": "invalid_token"},
        follow_redirects=False,
    )
    assert response.status_code == 401


def test_auth_disabled_allows_access(client):
    """When APP_PASSWORD is not set, all endpoints should be accessible."""
    if 'APP_PASSWORD' in os.environ:
        del os.environ['APP_PASSWORD']

    response = client.get("/api/config")
    assert response.status_code != 401

    root = client.get("/", follow_redirects=False)
    assert root.status_code in [302, 307]
    assert '/static/index.html' in _location(root)

    index = client.get("/static/index.html")
    assert index.status_code == 200


def test_verify_session_token():
    """Test session token verification."""
    os.environ['APP_PASSWORD'] = 'test_pass'

    valid_token = generate_session_token('test_pass')
    assert verify_session_token(valid_token) is True

    assert verify_session_token('invalid') is False

    del os.environ['APP_PASSWORD']


def test_verify_session_token_auth_disabled():
    """Session token verification should always succeed when auth is disabled."""
    if 'APP_PASSWORD' in os.environ:
        del os.environ['APP_PASSWORD']

    assert verify_session_token('any_token') is True


def test_static_files_served_when_auth_disabled(client):
    """When auth is disabled, static UI files remain open."""
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert response.status_code != 401


def test_root_redirects_to_ui(client):
    """Root path should redirect to UI when auth is disabled."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code in [302, 307]
    assert '/static/index.html' in _location(response)
