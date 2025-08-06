"""
routes/strava.py

API routes for Strava OAuth login, callback handling, account status, and disconnection.

Defines HTTP endpoints, manages the request/response flow for Strava 
authentication, and delegates database and sync logic to `crud/` and `services/`.
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, JSONResponse
from dependencies import get_db
from models.strava_user import StravaUser
from crud.user import create_or_get_strava_user
from services.user import get_current_user
from services.strava import sync_strava_data
from schemas.strava_user import StravaUserCreate
from datetime import datetime
import httpx
import os


router = APIRouter()

# Extracts the access token
# oauth2_scheme is for when the token is structured like Authorization: Bearer ...
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/login")
def login_strava(token: str = Depends(oauth2_scheme)):
    """
    Generates the Strava OAuth login URL with the user's JWT passed as state.

    Args:
        token (str): The JWT access token for the authenticated user (injected by `oauth2_scheme`).

    Returns:
        dict: The generated Strava OAuth authorization URL.

    Notes:
        - The frontend should redirect the user to this URL.
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

    Args:
        code (str): The authorization code returned by Strava after user login.

    Returns:
        dict: Token response data from Strava, including access and refresh tokens.
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
    Handle Strava OAuth callback after user login.

    Args:
        request (Request): The incoming request containing OAuth parameters.
        db (Session): The database session.

    Returns:
        RedirectResponse | JSONResponse: Redirects to the frontend or returns error JSON.

    Notes:
        - Strava redirects here after user login.
        - We extract the code and original JWT (state), verify the user,
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

        strava_user = create_or_get_strava_user(db, strava_user, token_data)

        await sync_strava_data(strava_user, strava_user.access_token, db)

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

    Args:
        token (str): The JWT access token for authentication (injected by `oauth2_scheme`).
        db (Session): The database session.

    Returns:
        dict: `{"connected": bool}` indicating Strava connection status.
    """
    try:
        user = get_current_user(db, token)
        strava_data = db.query(StravaUser).filter_by(user_id=user.id).first()

        # Return True only if a Strava record exists AND the user is connected
        return {"connected": bool(strava_data and strava_data.is_connected)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/disconnect")
def logout_strava(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Disconnects the user's Strava account by setting is_connected = False.

    Args:
        token (str): The JWT access token for authentication (injected by `oauth2_scheme`).
        db (Session): The database session.

    Returns:
        dict: A message indicating whether Strava was disconnected or not connected.

    Notes:
        - This also sends a POST request to Strava to revoke the user's access token
    """

    user = get_current_user(db, token)
    strava_data = db.query(StravaUser).filter_by(user_id=user.id).first()
    
    if strava_data:
        try:
            res = httpx.post(
                "https://www.strava.com/oauth/deauthorize",
                data={"access_token": strava_data.access_token},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            res.raise_for_status()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error while revoking Strava token: {str(e)}")

        strava_data.is_connected = False

        db.commit()
        db.refresh(strava_data)
        return {"message": "Strava disconnected"}

    return {"message": "Strava not connected"}