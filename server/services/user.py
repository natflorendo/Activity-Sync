# service user.py - user-related logic and integration
# This contains workflows that involve both database access and external services
# Created to prevent circular import when it came with google and jwt integration
from fastapi import HTTPException
from models.user import User
from sqlalchemy.orm import Session
import utils.jwt as jwt_utils, crud.user as user_crud
from datetime import datetime, timezone, timedelta
import os
import httpx

def get_current_user(db: Session, token: str):
    try:
        token = jwt_utils.refresh_jwt_token(token, db)
        user_id = jwt_utils.decode_jwt(token)
        user = user_crud.get_user_by_id(db, user_id)
        
        refresh_google_token(user, db)

        return user
    except Exception as e:
        raise Exception(status_code=500, detail=f"Failed to fetch user: {str(e)}")
    

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