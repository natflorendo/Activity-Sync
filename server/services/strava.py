# strava.py
from fastapi import APIRouter, Request, Depends, Header
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, JSONResponse
from datetime import datetime
import os
import httpx

from dependencies import get_db
import models.user as User
import crud.user as user_crud
from models.strava_user import StravaUser


router = APIRouter()

@router.get("/login")
def login_strava():
    return RedirectResponse(
        url=(
            "https://www.strava.com/oauth/authorize"
            f"?client_id={os.getenv('STRAVA_CLIENT_ID')}"
            "&response_type=code"
            f"&redirect_uri={os.getenv('BACKEND_URL')}/strava/callback"
            "&scope=read,activity:read_all"
            "&approval_prompt=force"
        )
    )

async def use_strava_code(code: str):
    async with httpx.AsyncClient() as client:
        res = await client.post("https://www.strava.com/oauth/token", data={
            "client_id": os.getenv("STRAVA_CLIENT_ID"),
            "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
            "code": code,
            "grant_type": "authorization_code"
        })
    
    return res.json()

@router.get("/callback")
async def strava_callback(
    request: Request,
    db: Session = Depends(get_db)
): 
    # current_user = user_crud.get_current_user(token, db)
    code = request.query_params.get("code")
    if not code:
        return JSONResponse(content={"error": "No code provided"}, status_code=400)
    
    try:
        token_data = await use_strava_code(code)
        
        # TODO: NEED TO GET USER ID (NEED TO DO GOOGLE OUTH)

        # Create or update StravaUser row
        # strava_user = db.query(StravaUser).filter_by(user_id=current_user.id).first()
        # if strava_user:
        #     strava_user.access_token = token_data["access_token"]
        #     strava_user.refresh_token = token_data["refresh_token"]
        #     strava_user.expires_at = datetime.fromtimestamp(token_data["expires_at"])
        # else:
        #     strava_user = StravaUser(
        #         user_id=current_user.id,
        #         id=token_data["athlete"]["id"],
        #         athelete_name=token_data["athlete"]["firstname"] + " " + token_data["athlete"]["lastname"],
        #         access_token=token_data["access_token"],
        #         refresh_token=token_data["refresh_token"],
        #         expires_at=datetime.fromtimestamp(token_data["expires_at"])
        #     )
        #     db.add(strava_user)

        # db.commit()
        return {
            "message": "Login successful",
            "token_data": token_data,
            "code": code,
        }
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)