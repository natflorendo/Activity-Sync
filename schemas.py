# schemas.py - Pydantic schemas: request/response validation and serialization
from pydantic import BaseModel
from uuid import UUID

class UserCreate(BaseModel):
    strava_id: str
    google_email: str
    strava_access_token: str
    google_access_token: str

class UserOut(BaseModel):
    id: UUID
    strava_id: str
    google_email: str

    # Allow reading from ORM objects (not just dicts)
    # Ex use case is response_model in main.py
    class Config:
        orm_mode = True