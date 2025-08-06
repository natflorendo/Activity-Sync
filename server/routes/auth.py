"""
routes/auth.py

API routes for authentication-related actions (validate, refresh, logout).

Defines HTTP endpoints and delegates logic to utilities or service functions.
"""
from fastapi import APIRouter, Response, Request, HTTPException, Depends 
from fastapi.security import OAuth2PasswordBearer
import utils.jwt as jwt_utils
from utils.cookies import delete_auth_cookies

router = APIRouter()

# oauth2_scheme is for when the token is structured like Authorization: Bearer ...
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/validate")
def validate_token(token: str = Depends(oauth2_scheme)):
    """
    Validate a JWT access token.

    Args:
        token (str): The JWT access token provided in the Authorization header.

    Returns:
        str: The user ID (sub) from the token if valid.
    """
    try:
        return jwt_utils.verify_jwt(token, expected_type="access")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
@router.post("/refresh")
def refresh_token(request: Request):
    """
    Refresh the JWT access token using a valid refresh token from cookies.

    Args:
        request (Request): The incoming request containing cookies.

    Returns:
        dict: A new short-lived access token.
    """
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
    """
    Log the user out by deleting authentication cookies.

    Args:
        response (Response): The response object to clear cookies from.

    Returns:
        dict: A message indicating successful logout.
    """
    delete_auth_cookies(response)

    return { "message": "Logged out"}