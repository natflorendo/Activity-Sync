# crud user.py - Pure data access: fetch, insert, update
# This contains pure database access functions only
from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate
from models.google_user import GoogleUser
from sqlalchemy.exc import IntegrityError

def create_or_get_user(db: Session, user: UserCreate):
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
            google_user = GoogleUser(
                email=user.google_data.email,
                sub=user.google_data.sub,
                access_token=user.google_data.access_token,
                access_token_expiry=user.google_data.access_token_expiry,
                refresh_token=user.google_data.refresh_token,
                refresh_token_expiry=user.google_data.refresh_token_expiry,
            )
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


def get_user_by_id(db: Session, user_id: str):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise ValueError("User not found")
        return user
    except Exception:
         raise Exception("Failed to fetch user by user_id")
    
def get_all_users(db: Session):
    try:
        return db.query(User).join(GoogleUser).all()
    except Exception as e:
        raise Exception(f"Failed to fetch all users: {e}")
    

# WORK IN PROGRESS
def get_user_by_strava_id(db: Session, strava_id: str):
    try:
        user = db.query(User).filter(User.strava_id == strava_id).first()
        if user is None:
            raise ValueError("User not found")
        return user
    except Exception:
         raise Exception("Failed to fetch user by strava_id")