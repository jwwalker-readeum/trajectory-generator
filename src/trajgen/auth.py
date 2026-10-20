"""Authentication middleware for demo service.

Simple password gate for single-user demo deployment.
Uses HTTP Basic Auth with session cookie for convenience.
"""

import os
import secrets
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers


# Session secret for cookie signing
SESSION_SECRET = secrets.token_urlsafe(32)

# Stable public URL for the login page (must match the route in api.py).
LOGIN_URL = '/login.html'

# Paths that don't require authentication.
# The main UI (/static/index.html, /static/app.js, /static/style.css) is NOT public.
# Login page CSS is inline in login.html; only the page itself is listed here.
PUBLIC_PATHS = {
    '/api/health',
    LOGIN_URL,
    '/login',
    '/api/login',
    '/favicon.ico',
    '/static/login.html',
}


def get_required_password() -> Optional[str]:
    """Get the required password from environment.
    
    Returns None if APP_PASSWORD is not set (auth disabled).
    """
    return os.environ.get('APP_PASSWORD')


def verify_session_token(token: str) -> bool:
    """Verify a session token.
    
    For this simple demo, we use a constant token derived from password + secret.
    In production, use signed JWT or proper session storage.
    """
    password = get_required_password()
    if password is None:
        return True  # Auth disabled
    
    expected_token = generate_session_token(password)
    return secrets.compare_digest(token, expected_token)


def generate_session_token(password: str) -> str:
    """Generate a session token for a valid password.
    
    Simple hash of password + session secret.
    In production, use proper JWT or session management.
    """
    import hashlib
    combined = f"{password}:{SESSION_SECRET}"
    return hashlib.sha256(combined.encode()).hexdigest()


class PasswordAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce password authentication.
    
    Supports both HTTP Basic Auth and session cookie.
    """
    
    async def dispatch(self, request: Request, call_next):
        password = get_required_password()
        
        # If no password configured, allow all
        if password is None:
            return await call_next(request)
        
        # Check if path is public (do not treat all of /static/ as public)
        path = request.url.path
        if path in PUBLIC_PATHS:
            return await call_next(request)
        
        # Check for valid session cookie
        session_token = request.cookies.get('session_token')
        if session_token and verify_session_token(session_token):
            return await call_next(request)
        
        # Check for HTTP Basic Auth
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Basic '):
            import base64
            try:
                encoded = auth_header.split(' ', 1)[1]
                decoded = base64.b64decode(encoded).decode('utf-8')
                username, provided_password = decoded.split(':', 1)
                
                if secrets.compare_digest(provided_password, password):
                    # Valid credentials, set session cookie
                    response = await call_next(request)
                    token = generate_session_token(password)
                    response.set_cookie(
                        key='session_token',
                        value=token,
                        httponly=True,
                        max_age=86400,  # 24 hours
                        samesite='lax'
                    )
                    return response
            except Exception:
                pass
        
        # Unauthorized - redirect to login or return 401
        if request.url.path.startswith('/api/'):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"},
                headers={"WWW-Authenticate": "Basic realm=\"Trajectory Generator\""}
            )
        else:
            # Redirect HTML requests to login page
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=LOGIN_URL, status_code=302)
