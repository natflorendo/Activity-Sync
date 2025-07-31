# strava.py
from fastapi import APIRouter, Request, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, JSONResponse
import os
import httpx
from dependencies import get_db
from models.strava_user import StravaUser
from crud.user import create_or_get_strava_user
from services.user import get_current_user
from schemas.strava_user import StravaUserCreate
from datetime import datetime


router = APIRouter()

# Extracts the access token
# oauth2_scheme is for when the token is structured like Authorization: Bearer ...
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/login")
def login_strava(token: str = Depends(oauth2_scheme)):
    """
    Generates the Strava OAuth login URL with the user's JWT passed as state.
    The frontend should redirect the user to this URL.
    """
    url=(
        "https://www.strava.com/oauth/authorize"
        f"?client_id={os.getenv('STRAVA_CLIENT_ID')}"
        "&response_type=code"
        f"&redirect_uri={os.getenv('BACKEND_URL')}/strava/callback"
        "&scope=read,activity:read_all"
        "&approval_prompt=force"
        f"&state={token}"
    )
    return {"url": url}

async def use_strava_code(code: str):
    """
    Exchanges the Strava authorization code for an access and refresh token.
    """
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
    """
    Strava redirects here after user login.
    We extract the code and original JWT (state), verify the user,
    then store their Strava access/refresh tokens in our DB.
    """
    code = request.query_params.get("code")
    state_token = request.query_params.get("state")

    if not code:
        return JSONResponse(content={"error": "No code provided"}, status_code=400)
    
    try:
        current_user = get_current_user(db, state_token)
        token_data = await use_strava_code(code)
        if not current_user:
            return JSONResponse(content={"error": "User not found"}, status_code=404)
        
        strava_user = StravaUserCreate(
            user_id=current_user.id,
            athlete_id=str(token_data["athlete"]["id"]),
            athlete_name=token_data["athlete"]["firstname"] + " " + token_data["athlete"]["lastname"],
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_at=datetime.fromtimestamp(token_data["expires_at"])
        )

        create_or_get_strava_user(db, strava_user, token_data)

        response = RedirectResponse(url=os.getenv("FRONTEND_URL"))

        return response
        
        return {
            "message": "Login successful",
            "token_data": token_data,
            "code": code,
            "token": state_token
        }
    except Exception:
        return RedirectResponse(url=os.getenv("FRONTEND_URL"))
    
@router.get("/status")
def strava_status(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Checks if the user is connected to Strava.
    """
    try:
        user = get_current_user(db, token)
        strava_data = db.query(StravaUser).filter_by(user_id=user.id).first()

        # Return True only if a Strava record exists AND the user is connected
        return {"connected": bool(strava_data and strava_data.is_connected)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Unexpected error: {str(e)}"})

@router.post("/disconnect")
def logout_strava(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Disconnects the user's Strava account by setting is_connected = False.
    This also sends a request to Strava to revoke the access token
    """
    user = get_current_user(db, token)
    strava_data = db.query(StravaUser).filter_by(user_id=user.id).first()
    
    if strava_data:
        try:
            res = httpx.post(
                "https://www.strava.com/oauth/deauthorize",
                headers={"Authorization": f"Bearer {strava_data.access_token}"}
            )
            if res.status_code != 200:
                print("Warning: Failed to revoke token on Strava")
        except Exception as e:
            print(f"Error while revoking Strava token: {e}")

        strava_data.is_connected = False
        db.commit()
        db.refresh(strava_data)
        return {"messgage": "Strava disconnected"}

    return {"message": "Strava not connected"}