"""
Database connection and migrations.
"""

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

load_dotenv()

# Base class for declarative models
Base = declarative_base()
metadata = MetaData()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/et_heatmap.db")

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific settings
    os.makedirs("data", exist_ok=True)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # Postgres settings
    engine = create_engine(DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Database session dependency for FastAPI.
    Yields a database session and closes it after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """
    Get a database session for use outside FastAPI.
    Remember to close it when done: session.close()
    """
    return SessionLocal()


def init_db():
    """
    Initialize database by running migrations.
    """
    from scripts.migrate_db import run_migrations
    run_migrations(DATABASE_URL)


def test_connection():
    """
    Test database connection.
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test connection
    if test_connection():
        print("Database connection successful!")
    else:
        print("Database connection failed!")
        print(f"Trying to initialize database at: {DATABASE_URL}")
        init_db()
