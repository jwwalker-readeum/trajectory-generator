"""Tests for authentication middleware."""

import os
import pytest
from fastapi.testclient import TestClient
from src.trajgen.api import app
from src.trajgen.auth import generate_session_token, verify_session_token


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


def test_health_endpoint_public(client):
    """Health endpoint should be accessible without auth."""
    response = client.get("/api/health")
    # Should not be 401 (auth error), even if service is not initialized (503)
    assert response.status_code != 401


def test_public_paths_without_auth(client, auth_enabled):
    """Public paths should be accessible even when auth is enabled."""
    # Health endpoint - should not return 401 even if service unavailable
    response = client.get("/api/health")
    assert response.status_code != 401
    
    # Login page should be accessible
    response = client.get("/login.html")
    # Returns 404 since it's a static file, but not 401/302
    assert response.status_code in [404, 200]


def test_protected_api_requires_auth(client, auth_enabled):
    """Protected API endpoints should require authentication."""
    # Config endpoint should either be 401 (no auth) or redirect
    # Since auth is enabled, it should not allow access
    response = client.get("/api/config", follow_redirects=False)
    # Should be 401 or 302 (redirect), not 200 or 503
    assert response.status_code in [401, 302]


def test_login_with_correct_password(client, auth_enabled):
    """Login should succeed with correct password."""
    response = client.post("/api/login", data={"password": "test_password_123"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "session_token" in response.cookies


def test_login_with_incorrect_password(client, auth_enabled):
    """Login should fail with incorrect password."""
    response = client.post("/api/login", data={"password": "wrong_password"})
    assert response.status_code == 401


def test_session_token_grants_access(client, auth_enabled):
    """Valid session token should grant access to protected endpoints."""
    # Get session token
    token = generate_session_token("test_password_123")
    
    # Access protected endpoint with session token
    response = client.get("/api/config", cookies={"session_token": token})
    # Should not be 401
    assert response.status_code != 401


def test_invalid_session_token_denies_access(client, auth_enabled):
    """Invalid session token should not grant access."""
    response = client.get("/api/config", cookies={"session_token": "invalid_token"}, follow_redirects=False)
    # Should be 401 or 302 (redirect), not 200 or 503
    assert response.status_code in [401, 302]


def test_auth_disabled_allows_access(client):
    """When APP_PASSWORD is not set, all endpoints should be accessible."""
    # Ensure APP_PASSWORD is not set
    if 'APP_PASSWORD' in os.environ:
        del os.environ['APP_PASSWORD']
    
    response = client.get("/api/config")
    # Should not be 401 (might be 503 if service not initialized, but not auth error)
    assert response.status_code != 401


def test_verify_session_token():
    """Test session token verification."""
    # Set password
    os.environ['APP_PASSWORD'] = 'test_pass'
    
    # Generate valid token
    valid_token = generate_session_token('test_pass')
    assert verify_session_token(valid_token) is True
    
    # Test invalid token
    assert verify_session_token('invalid') is False
    
    # Cleanup
    del os.environ['APP_PASSWORD']


def test_verify_session_token_auth_disabled():
    """Session token verification should always succeed when auth is disabled."""
    # Ensure no password set
    if 'APP_PASSWORD' in os.environ:
        del os.environ['APP_PASSWORD']
    
    # Any token should be valid when auth is disabled
    assert verify_session_token('any_token') is True


def test_static_files_served_without_auth(client):
    """Static files should be accessible without authentication."""
    # This test assumes static files exist
    # In real deployment, CSS/JS should be accessible
    response = client.get("/static/style.css")
    # 404 if file doesn't exist during test, 200 if it does
    # But should NOT be 401 or redirect to login
    assert response.status_code in [200, 404]
    assert response.status_code != 401


def test_root_redirects_to_ui(client):
    """Root path should redirect to UI."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code in [302, 307]
    assert '/static/index.html' in response.headers.get('location', '')
