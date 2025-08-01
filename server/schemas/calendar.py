from pydantic import BaseModel
from datetime import datetime

class CalendarEventCreate(BaseModel):
    summary: str
    description: str
    start_time: datetime
    end_time: datetime
    time_zone: str = "America/Chicago"