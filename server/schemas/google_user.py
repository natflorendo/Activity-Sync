"""
schemas/google_user.py

Pydantic schemas for Google OAuth user data.

Defines request/response models and contains no business logic or database code.
"""
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class GoogleUserCreate(BaseModel):
    email: str
    sub: str
    access_token: str
    access_token_expiry: datetime
    refresh_token: str
    refresh_token_expiry: datetime | None = None

class GoogleUserOut(BaseModel):
    id: UUID
    email: str
    sub: str
    access_token: str
    access_token_expiry: datetime
    refresh_token: str
    refresh_token_expiry: datetime | None

    model_config = ConfigDict(from_attributes=True)