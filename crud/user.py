# crud user.py - Pure data access: fetch, insert, update
from sqlalchemy.orm import Session
from models import User
from schemas.user import UserCreate
from sqlalchemy.exc import IntegrityError

def create_user(db: Session, user: UserCreate):
    existing = db.query(User).filter(
        (User.google_email == user.google_email) | (User.strava_id == user.strava_id)
    ).first()
    if existing:
        raise ValueError("User with this email or Strava ID already exists")
    
    try:
        # ** unpacks from dictionary to keyword arguments
        db_user = User(**user.model_dump())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("Possibly invalid data")
    except Exception:
        db.rollback()
        raise Exception("Unexpected error while creating user")

def get_user_by_strava_id(db: Session, strava_id: str):
    try:
        user = db.query(User).filter(User.strava_id == strava_id).first()
        if user is None:
            raise ValueError("User not found")
        return user
    except Exception:
         raise Exception("Failed to fetch user by strava_id")