from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.coupon import Base
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PostgreSQL database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/coupons_db"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session with transaction management"""
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Commit if no exception
    except Exception:
        db.rollback()  # Rollback on any exception
        raise
    finally:
        db.close()
