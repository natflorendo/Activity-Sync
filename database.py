# database.py - Database connection setup and session management
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env file")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,    # Ensures that connections are alive before using them
    pool_size=5,           # Keep 5 persistent connections open in the pool
    max_overflow=5         # # Allow up to 5 temporary extra connections during traffic spikes
)

SessionLocal = sessionmaker(
    autocommit=False,     # Don’t auto-commit transactions — must call db.commit()
    autoflush=False,      # Don't automatically send uncommitted changes to the database before calling commit()
    bind=engine           # Bind the session to database engine
)
# Base class for all ORM models 
# all tables should inherit from this to be registered with SQLAlchemy
Base = declarative_base()