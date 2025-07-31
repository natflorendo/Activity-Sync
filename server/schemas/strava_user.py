from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class StravaUserCreate(BaseModel):
    user_id: UUID
    athlete_id: str
    athlete_name: str
    access_token: str
    refresh_token: str
    expires_at: datetime

class StravaUserOut(BaseModel):
    id: UUID
    athlete_id: str
    athlete_name: str
    expires_at: datetime
    access_token: str #DELETE ME: used for testing in postman
    is_connected: bool

    model_config = ConfigDict(from_attributes=True)