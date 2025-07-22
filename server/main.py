# main.py - Request handling: user interaction, errors
from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from database import Base, engine
from dependencies import get_db
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from services.strava import router as strava_router
from services.google import router as google_router
import services.user as user_service
import crud.user as user_crud, schemas.user as user_schemas
from dotenv import load_dotenv
import os
import logging
import models # triggers models/__init__.py to load all models

load_dotenv()
JWT_ALGORITHM = "HS256"

allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
ENV = os.getenv("NODE_ENV", "production").lower()

# Set up logging config based on environment
if ENV == "development":
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Needed for AuthLib
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET"))

app.include_router(strava_router, prefix="/strava")
app.include_router(google_router, prefix="/google")

# Drop all tables (needed for development to reset database)
# Base.metadata.drop_all(bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


# Create a user
@app.post("/users/", response_model=user_schemas.UserOut)
def create_user(user: user_schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        return user_crud.create_or_get_user(db, user)
    except ValueError as e:
        logger.warning(f"User creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during user creation")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Get current user
@app.get("/users/me", response_model=user_schemas.UserOut)
def get_current_user(token: str = Header(...), db: Session = Depends(get_db)):
    try:
        return user_service.get_current_user(db, token)
    except Exception as e:
        logger.exception("Error fetching current user")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Get all users
@app.get("/users/", response_model=list[user_schemas.UserOut])
def get_all_users(db: Session = Depends(get_db)):
    try:
        return user_crud.get_all_users(db)
    except Exception as e:
        logger.exception("Unexpected error while fetching all users")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# WORK IN PROGRESS
@app.get("/users/strava/{strava_id}", response_model=user_schemas.UserOut)
def get_user_by_strava_id(strava_id: str, db: Session = Depends(get_db)):
    try:
        return user_crud.get_user_by_strava_id(db, strava_id) 
    except ValueError as e:
        logger.info(f"User not found for strava_id={strava_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error while fetching user by strava_id")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")