import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from main import app # Import your FastAPI app
from dependencies import get_db
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env file")

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for each test."""
    connection = engine.connect()  # Open a raw DB connection
    # Begin a transaction (isolates all DB changes until committed or rolled back)
    transaction = connection.begin()

    db = TestingSessionLocal(bind=connection)
    try:
        yield db
    finally:
        db.close() # Close the session
        transaction.rollback()  # Undo any DB changes made during the test
        connection.close() # Close the raw connection

@pytest.fixture(scope="function")
def client(db_session):
    """Inject the rollback-safe DB session into FastAPI"""

    # Override the get_db function to use our test session
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    # Creates a test client to simulate real HTTP requests without starting a server
    return TestClient(app)