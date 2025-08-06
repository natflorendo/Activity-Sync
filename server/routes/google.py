"""
routes/google.py

API routes for Google OAuth login and callback handling.

Defines HTTP endpoints, manages request/response flow, and 
delegates database and token logic to `crud/` and `utils/`.
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from dependencies import get_db
from authlib.integrations.starlette_client import OAuth
from schemas.user import UserCreate
from schemas.google_user import GoogleUserCreate
from crud.user import create_or_get_user
from utils.cookies import set_auth_cookies
import utils.jwt as jwt_utils
from datetime import datetime, timezone, timedelta
import os


router = APIRouter()


oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    # Scope is optional here, but sets default scope
    client_kwargs={'scope': 'openid email profile https://www.googleapis.com/auth/calendar.events'}
)

@router.get("/login")
async def login_google(request: Request):
    """
    Redirect user to Google OAuth login and consent screen

    Args:
        request (Request): The incoming request object.

    Returns:
        RedirectResponse: A redirect to Google's OAuth authorization page.
    """
    redirect_uri = f"{os.getenv('BACKEND_URL')}/google/callback"
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        prompt="consent",          # always show consent screen
        # Request offline access so we automatically receive a refresh_token
        # allows the app to refresh the access_token without user logging in again
        access_type="offline", 
        # Explicitly defines scope for the consent screen
        scope=(
            "openid email profile "
            "https://www.googleapis.com/auth/calendar" # Full access to calendars (list, create, edit calendars + events)
        ),
    )

@router.get("/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle Google's OAuth callback after user login.

    Args:
        request (Request): The incoming request containing OAuth parameters.
        db (Session): The database session.

    Returns:
        RedirectResponse: Redirects the user to the frontend after login.
    
    Notes:
        - Google redirects here after user login.
        - We exchange the authorization code for tokens using Authlib, 
        stores or updates the user in the database with Google account info,
        issues JWT access/refresh tokens, and sets authentication cookies in the response.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
        if not token:
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")
        
        user_info = token["userinfo"]
        refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token["refresh_token_expires_in"])

        user_data = UserCreate(
            name=user_info["name"],
            google_data=GoogleUserCreate(
                email=user_info["email"],
                sub=user_info["sub"],
                access_token=token["access_token"],
                access_token_expiry=datetime.fromtimestamp(token["expires_at"], tz=timezone.utc),
                refresh_token=token.get("refresh_token"),
                refresh_token_expiry=refresh_token_expires_at,
            )
        )
        
        user = create_or_get_user(db=db, user=user_data)

        # Create access and refresh token
        access_token = jwt_utils.create_access_token(user.id)
        refresh_token = jwt_utils.create_refresh_token(user.id)

        # Redirect Response only works if you did window.location.href
        response = RedirectResponse(url=os.getenv("FRONTEND_URL"))
        set_auth_cookies(response, access_token, refresh_token)

        return response

        return {
            "message": "Login successful", 
            "token_type": "Bearer",
            "token": token, 
            "user": user
            }
    except Exception:
        return RedirectResponse(url=os.getenv("FRONTEND_URL"))