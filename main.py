# main.py - Request handling: user interaction, errors
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base
from fastapi.middleware.cors import CORSMiddleware
import crud, schemas
from dotenv import load_dotenv
import os
import logging


load_dotenv()

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
    allow_origins=allowed_origins,  # Allows all origins, adjust as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, adjust as needed
    allow_headers=["*"],  # Allows all headers, adjust as needed
)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_user(db, user)
    except ValueError as e:
        logger.warning(f"User creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during user creation")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
@app.get("/users/strava/{strava_id}", response_model=schemas.UserOut)
def get_user_by_strava_id(strava_id: str, db: Session = Depends(get_db)):
    try:
        return crud.get_user_by_strava_id(db, strava_id) 
    except ValueError as e:
        logger.info(f"User not found for strava_id={strava_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error while fetching user by strava_id")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")