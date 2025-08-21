"""
utils/cookies.py

Helper functions for setting and deleting authentication cookies.

Contains small, reusable, stateless functions with no business logic or database access.
"""
from fastapi import Response
import os

IS_DEV = os.getenv("NODE_ENV").lower() == "development"
COOKIE_SAMESITE = "lax" if IS_DEV else "none"
COOKIE_SECURE = False if IS_DEV else True
COOKIE_DOMAIN = os.getenv("BACKEND_DOMAIN")

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """
    Sets Authentiation cookies on HTTP response

    Args:
        response (Response): The FastAPI response object to attach cookies to.
        access_token (str): The short-lived JWT access token for API access.
        refresh_token (str): The long-lived JWT refresh token for session persistence.

    Returns:
        None
    """
    # HTTP-only refresh token cookie for session persistence.
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,  # Only over HTTPS (False in dev [http])
        samesite=COOKIE_SAMESITE,  # Allows redirect-based auth
        max_age=60 * 60 * 24 * 30, # 30 days
        path="/",
        domain=COOKIE_DOMAIN
    )

    # JS-readable access token cookie for short-term API access
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=False, # JavaScript can read this
        secure=COOKIE_SECURE, # Set False for development (http)
        samesite=COOKIE_SAMESITE,
        max_age=60 * 5,  # 5 minutes
        path="/",
        domain=COOKIE_DOMAIN
    )

def delete_auth_cookies(response: Response):
    """
    Deletes Authentication cookies. Intended to be called on logout or session expiration.

    Args:
        response (Response): The FastAPI response object to clear cookies from.

    Returns:
        None
    """
    # Just in case to prevent stale cookies from being reused or lingering in the browser.
    response.delete_cookie(
        key="access_token",
        httponly=False, 
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
        domain=COOKIE_DOMAIN
    )
    
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
        domain=COOKIE_DOMAIN
    )