from fastapi import HTTPException
from sqlalchemy.orm import Session
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timezone, timedelta
import os


JWT_ALGORITHM = "HS256"

# Create a JWT token for the user
def create_jwt_token(user_id: str):
    """Create a JWT token for the user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(hours=1)  # Token valid for 1 hour
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm=JWT_ALGORITHM)

# Decode a JWT token to get the user ID
def decode_jwt(token: str):
    """Decode a JWT token and return the user ID."""
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=[JWT_ALGORITHM])
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