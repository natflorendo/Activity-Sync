# model user.py - SQLAlchemy ORM models: table structure and relationships
import uuid
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import Column, String, DateTime
from database import Base
from sqlalchemy.orm import relationship
import os

# User model
class User(Base):
    __tablename__ = 'users'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    jwt_token=Column(String, nullable=True)

    # One-to-one relationships
    # Lazy loads GoogleUser via SQL JOIN when querying User
    google_data = relationship("GoogleUser", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="joined")
    strava_data = relationship("StravaUser", back_populates="user", uselist=False, cascade="all, delete-orphan")

    if os.getenv("NODE_ENV") == "development":
        def __repr__(self):
            return f"<User(id={self.id}, strava_id={self.strava_id}, google_email={self.google_email})>"
        