from fastapi import APIRouter, Response, Request, HTTPException, Depends 
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import utils.jwt as jwt_utils
from utils.cookies import delete_auth_cookies
from dependencies import get_db
import os

router = APIRouter()

# oauth2_scheme is for when the token is structured like Authorization: Bearer ...
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/validate")
def validate_token(token: str = Depends(oauth2_scheme)):
    try:
        return jwt_utils.verify_jwt(token, expected_type="access")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
@router.post("/refresh")
def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token found in cookies")
    try:
        new_access_Token = jwt_utils.refresh_jwt_token(refresh_token)
        return {"access_token": new_access_Token}
    except HTTPException as e:
        raise e
    except HTTPException as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/logout")
def logout(response: Response):
    delete_auth_cookies(response)

    return { "message": "Logged out"}