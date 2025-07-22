# google.py
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from dependencies import get_db
from authlib.integrations.starlette_client import OAuth
from schemas.user import UserCreate
from schemas.google_user import GoogleUserCreate
from crud.user import create_or_get_user
import utils.jwt as jwt_utils
from datetime import datetime, timezone, timedelta
import os
import httpx


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

# Redirect user to Google OAuth
@router.get("/auth")
async def login_google(request: Request):
    redirect_uri = f"{os.getenv('BACKEND_URL')}/google/auth/callback"
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        prompt="consent",          # always show consent screen
        # Request offline access so we automatically receive a refresh_token
        # allows the app to refresh the access_token without user logging in again
        access_type="offline", 
        # Explicitly defines scope for the consent screen
        scope=(
            "openid email profile https://www.googleapis.com/auth/calendar.events"
        ),
    )

# Handle Google Callback
@router.get("/auth/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
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

        access_token = jwt_utils.create_access_token(user.id)
        refresh_token = jwt_utils.create_refresh_token(user.id)

        response = RedirectResponse(url=os.getenv("FRONTEND_URL"))
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # Only over HTTPS
            samesite="Lax",  # Allows redirect-based auth
            max_age=3600
        )

        # JS-readable access token cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=False, # JavaScript can read this
            secure=True, # Set False for development (http)
            samesite="Lax",
            max_age=300,  # 5 minutes
            path="/"
        )

        return response

        return {
            "message": "Login successful", 
            "token_type": "Bearer",
            "token": token, 
            "user": user
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google OAuth failed: {str(e)}")
    
@router.post("/auth/logout")
def logout(response: Response):
    # Just in case to prevent stale cookies from being reused or lingering in the browser.
    response.delete_cookie(
        key="access_token",
        path="/"
    )
    
    response.delete_cookie(
        key="refresh_token",
        path="/"
    )

    return { "message": "Logged out"}