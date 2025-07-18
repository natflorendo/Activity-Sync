# models.py - SQLAlchemy ORM models: table structure and relationships
import uuid
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import Column, String
from database import Base
from dotenv import load_dotenv
import os

load_dotenv()


# User model
class User(Base):
    __tablename__ = 'users'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    strava_id = Column(String, unique=True, index=True)
    google_email = Column(String, unique=True, index=True)
    strava_access_token = Column(String)
    google_access_token = Column(String)

    if os.getenv("NODE_ENV") == "development":
        def __repr__(self):
            return f"<User(id={self.id}, strava_id={self.strava_id}, google_email={self.google_email})>"