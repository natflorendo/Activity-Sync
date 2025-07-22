# strava_user.py 
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base
import os

class GoogleUser(Base):
    __tablename__ = 'google_users'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    sub = Column(String, unique=True, index=True)
    access_token = Column(String)
    access_token_expiry = Column(DateTime(timezone=True))
    refresh_token = Column(String)
    refresh_token_expiry = Column(DateTime(timezone=True))

    # One-to-One relationship with User
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), unique=True)
    user = relationship("User", back_populates="google_data")

    if os.getenv("NODE_ENV") == "development":
        def __repr__(self):
            return (
                f"<GoogleUser("
                f"id={self.id}, "
                f"email={self.email}, "
                f"sub={self.sub}, "
                f"access_token={self.access_token}, "
                f"access_token_expiry={self.access_token_expiry}, "
                f"refresh_token={self.refresh_token}, "
                f"refresh_token_expiry={self.refresh_token_expiry}, "
                f"user_id={self.user_id}"
                ")>"
            )