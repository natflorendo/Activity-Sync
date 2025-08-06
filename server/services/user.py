"""
services/user.py


Business logic for user-related workflows, including token validation
and refreshing Google and Strava OAuth tokens.

Coordinates database access, JWT verification, and external API calls.

Created to prevent circular import when it came with google and jwt integration
"""
from fastapi import HTTPException
from models.user import User
from sqlalchemy.orm import Session
import utils.jwt as jwt_utils, crud.user as user_crud
from datetime import datetime, timezone, timedelta
import os
import httpx

def get_current_user(db: Session, token: str):
    """
    Retrieve the currently authenticated user and refresh their OAuth tokens.

    Args:
        db (Session): The database session.
        token (str): The JWT access token for authentication.

    Returns:
        User: The authenticated user object.
    """
    try:
        user_id = jwt_utils.verify_jwt(token, "access")
        user = user_crud.get_user_by_id(db, user_id)
        
        refresh_google_token(user, db)
        refresh_strava_token(user, db)

        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user: {str(e)}")
    

def refresh_google_token(user: User, db: Session):
    """
    Refresh the Google OAuth access token.
    
    Args:
        user (User): The user whose Google token should be refreshed.
        db (Session): The database session.

    Returns:
        str: The valid Google access token.
    """
    google_data = user.google_data

    if not google_data:
        raise ValueError("User does not have Google OAuth data")
    
    now = datetime.now(timezone.utc)
    # Token still valid
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
        raise HTTPException(status_code=500, detail=f"HTTP error while refreshing google token: {str(e)}")
    
def refresh_strava_token(user: User, db: Session):
    """
    Refresh the Strava OAuth access token

    Args:
        user (User): The user whose Strava token should be refreshed.
        db (Session): The database session.

    Returns:
        str | None: The valid Strava access token, or None if the user has no Strava data.
    """
    strava_data = user.strava_data

    if not strava_data:
        # User does not have Strava OAuth data
        return
    
    now = datetime.now(timezone.utc)
    # Token still valid
    if strava_data.expires_at and strava_data.expires_at > now:
        return
    
    data = {
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
        "refresh_token": strava_data.refresh_token,
        "grant_type": "refresh_token"
    }

    try:
        response = httpx.post("https://www.strava.com/oauth/token", data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to refresh Strava token")
        token = response.json()

        strava_data.access_token = token["access_token"]
        strava_data.refresh_token = token["refresh_token"]
        strava_data.expires_at = datetime.fromtimestamp(token["expires_at"], tz=timezone.utc)

        db.commit()
        db.refresh(strava_data)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP error while refreshing Strava token: {str(e)}")