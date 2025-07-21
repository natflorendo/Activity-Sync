# schemas google_user.py - Pydantic schemas for Google OAuth user data
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class GoogleUserCreate(BaseModel):
    email: str
    sub: str
    access_token: str
    access_token_expiry: datetime
    refresh_token: str
    refresh_token_expiry: datetime

class GoogleUserOut(BaseModel):
    email: str
    sub: str
    access_token_expiry: datetime
    refresh_token_expiry: datetime

    model_config = ConfigDict(from_attributes=True)