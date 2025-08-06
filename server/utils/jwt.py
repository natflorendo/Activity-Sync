"""
utils/jwt.py

Helper functions for creating, verifying, and refreshing JWT tokens.

Contains small, reusable, stateless functions with no business logic or database access.
"""
from fastapi import HTTPException
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timezone, timedelta
import os


JWT_ALGORITHM = "HS256"

# Create a JWT access token for the user
def create_access_token(user_id: str):
    """
    Create a JWT access token for the user.
    
    Args:
        user_id (str): The unique ID of the user.

    Returns:
        str: The encoded JWT access token.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=5)  # Token valid for 5 minutes
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm=JWT_ALGORITHM)

# Create a JWT refresh token for the user
def create_refresh_token(user_id: str):
    """
    Create a JWT refresh token for the user.

    Args:
        user_id (str): The unique ID of the user.

    Returns:
        str: The encoded JWT refresh token.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=30)  # Token valid for 1 month
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm=JWT_ALGORITHM)

# Decode a JWT token to get the user ID and verify type
def verify_jwt(token: str, expected_type: str):
    """
    Decode a JWT token and return the user ID and verify type.
    
    Args:
        token (str): The JWT token to verify.
        expected_type (str): The expected token type ("access" or "refresh").

    Returns:
        str: The user ID (`sub`) embedded in the token.
    """
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            raise HTTPException(status_code=401, detail=f"Expected {expected_type} token")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
# Refresh a JWT access token if it has expired
def refresh_jwt_token(token: str):
    """
    Return the original token if valid, otherwise issue a refreshed one.
    
    Args:
        token (str): The JWT refresh token.

    Returns:
        str: A new JWT access token.
    """
    try:
        # Suceeds if the token is valid and not expired
        user_id = verify_jwt(token, expected_type="refresh")
        return create_access_token(user_id)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # TODO Want to add how google extends token access via refresh token usage
    # Refresh token implementation fix