# strava_user.py 
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base
import os

class StravaUser(Base):
    __tablename__ = 'strava_users'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    athlete_name = Column(String, index=True)
    strava_id = Column(String, unique=True, index=True)
    access_token = Column(String)
    refresh_token = Column(String)
    expires_at = Column(DateTime)

    # One-to-One relationship with User
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), unique=True)
    user = relationship("User", back_populates="strava_data")

    if os.getenv("NODE_ENV") == "development":
        def __repr__(self):
            return f"<StravaUser(id={self.id}, strava_id={self.strava_id})>"