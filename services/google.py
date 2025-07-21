# google.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from models.user import User
from dependencies import get_db
from authlib.integrations.starlette_client import OAuth
from schemas.user import UserCreate
from schemas.google_user import GoogleUserCreate
from crud.user import create_or_get_user
from datetime import datetime, timezone, timedelta
from utils.jwt import create_jwt_token
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

def refresh_google_token(user: User, db: Session):
    """Refresh the Google OAuth token."""
    google_data = user.google_data

    if not google_data:
        raise ValueError("User does not have Google OAuth data")
    
    now = datetime.now(timezone.utc)
    if google_data.access_token_expiry and google_data.access_token_expiry > now:
        return google_data.access_token
    
    data = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "refresh_token": google_data.refresh_token,
        "grant_type": "refresh_token"
    }

    try:
        response = httpx.post("https://oauth2.googleapis.com/token", data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to refresh Google token")
        token = response.json()

        google_data.access_token = token["access_token"]
        google_data.access_token_expiry = now + timedelta(seconds=token["expires_in"])

        db.commit()
        db.refresh(google_data)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP error while refreshing token: {str(e)}")


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

        #TODO: Set JWT token in cookies and return it in response (when frontnend is ready)
        # response = RedirectResponse(url=os.getenv("FRONTEND_URL"))
        # response.set_cookie(
        #     key="access_token",
        #     value=jwt_token,
        #     httponly=True,
        #     secure=True,  # Only over HTTPS
        #     samesite="Lax",  # Or "Strict" depending on your frontend
        #     max_age=3600
        # )
        # return response

        return {
            "message": "Login successful", 
            "token_type": "Bearer",
            "token": token, 
            "user": user
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google OAuth failed: {str(e)}")