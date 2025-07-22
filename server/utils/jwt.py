from fastapi import HTTPException
from sqlalchemy.orm import Session
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timezone, timedelta
import os


JWT_ALGORITHM = "HS256"

# Create a JWT access token for the user
def create_access_token(user_id: str):
    """Create a JWT access token for the user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=15)  # Token valid for 15 minues
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm=JWT_ALGORITHM)

# Create a JWT refresh token for the user
def create_refresh_token(user_id: str):
    """Create a JWT refresh token for the user."""
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
    """Decode a JWT token and return the user ID and verify type."""
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
    
# Refresh a JWT token if it has expired
# Allows the app to work continuously in the background without having to log in again.
# Continues to function as long as the user hasn't logged out or revoked access.
# Probably will DELETE LATER
def refresh_jwt_token(token: str, db: Session):
    """Return the original token if valid, otherwise issue a refreshed one."""
    try:
        # Try normal decode
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        # Decode without verifying exp to get the user ID
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET"),
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False}
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Check if user logged out (tokens made before get revoked)
        # iat = datetime.fromtimestamp(payload["iat"])
        # user = get_user_by_id(db, user_id)
        # if user.jwt_revoked_at and iat < user.jwt_revoked_at:
            # raise HTTPException(status_code=401, detail="Token revoked")
        
        return create_jwt_token(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")