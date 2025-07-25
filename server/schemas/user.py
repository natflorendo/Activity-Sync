# schemas user.py - Pydantic schemas: request/response validation and serialization
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID
from schemas.google_user import GoogleUserCreate, GoogleUserOut

class UserCreate(BaseModel):
    name: str
    google_data: GoogleUserCreate

class UserOut(BaseModel):
    id: UUID
    name: str
    google_data: GoogleUserOut


    # Allow reading from ORM objects (not just dicts)
    # Example use case is response_model in main.py
    model_config = ConfigDict(from_attributes=True)