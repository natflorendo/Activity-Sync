"""
crud/user.py - Pure data access: fetch, insert, update

This contains pure database access functions only for 
User-related tables (User, GoogleUser, StravaUser).
"""
from sqlalchemy.orm import Session
from schemas.user import UserCreate
from schemas.strava_user import StravaUserCreate
from models.user import User
from models.google_user import GoogleUser
from models.strava_user import StravaUser
from sqlalchemy.exc import IntegrityError
import os

def create_or_get_user(db: Session, user: UserCreate):
    """
    Create or update a User record along with its linked GoogleUser.

    Args:
        db (Session): SQLAlchemy database session.
        user (UserCreate): Pydantic schema containing user and Google user data.

    Returns:
        User: The created or updated User ORM object.
    """
    try:
        # Use sub because there is no id when first creating an account
        db_google_user = db.query(GoogleUser).filter_by(sub=user.google_data.sub).first()

        if db_google_user:
            db_google_user.access_token = user.google_data.access_token
            db_google_user.access_token_expiry = user.google_data.access_token_expiry
            db_google_user.refresh_token = user.google_data.refresh_token
            db_google_user.refresh_token_expiry = user.google_data.refresh_token_expiry

            # Get user via foreign key
            db_user = db.query(User).filter_by(id=db_google_user.user_id).first()
        else:
            # Create new User and linked GoogleUser
            # Create SQLAlchemy models, not Pydantic schemas
            google_user = GoogleUser(**user.google_data.model_dump())
            # You can't use **user.model_dump() directly here because 
            # user.model_dump() returns a nested dictionary for google_data
            # But the SQLAlchemy User model expects google_data to be a GoogleUser ORM instance
            db_user = User(
                name=user.name,
                google_data=google_user
            )
            db.add(db_user)

        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("Possibly invalid data")
    except Exception as e:
        db.rollback()
        raise Exception(f"Unexpected error while creating user: {str(e)}")

def create_or_get_strava_user(db: Session, strava_user: StravaUserCreate, token_data: dict):
    """
    Create or update a StravaUser record.

    Args:
        db (Session): SQLAlchemy database session.
        strava_user (StravaUserCreate): Pydantic schema containing Strava user data.
        token_data (dict): Raw token data returned by Strava's OAuth API.

    Returns:
        StravaUser: The created or updated StravaUser ORM object.
    """
    try:
       # Create or update StravaUser row
        db_strava_user = db.query(StravaUser).filter_by(user_id=strava_user.user_id).first()
        if db_strava_user:
            # Update existing tokens
            db_strava_user.access_token = strava_user.access_token
            db_strava_user.refresh_token = strava_user.refresh_token
            db_strava_user.expires_at = strava_user.expires_at
            db_strava_user.is_connected = True
        else:
            # create new StravaUser row
            db_strava_user = StravaUser(**strava_user.model_dump())
            db.add(db_strava_user)

        db.commit()
        db.refresh(db_strava_user)
        return db_strava_user
    except IntegrityError:
        db.rollback()
        raise ValueError("Possibly invalid data")
    except Exception as e:
        db.rollback()
        raise Exception(f"Unexpected error while creating strava user: {str(e)}")


def get_user_by_id(db: Session, user_id: str):
    """
    Fetch a User by their unique ID.

    Args:
        db (Session): SQLAlchemy database session.
        user_id (str): The unique ID of the user.

    Returns:
        User: The matching User ORM object.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise ValueError("User not found")
        return user
    except Exception:
         raise Exception("Failed to fetch user by user_id")


def get_all_users(db: Session):
    """
    Fetch all users from the database (development mode only).

    Args:
        db (Session): SQLAlchemy database session.

    Returns:
        list[User]: List of all User ORM objects.
    """
    if os.getenv("NODE_ENV") != "development":
        raise PermissionError("Fetching all users is restricted to development mode")
    
    try:
        return db.query(User).all()
    except Exception as e:
        raise Exception(f"Failed to fetch all users: {e}")