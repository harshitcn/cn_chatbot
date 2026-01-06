"""
Database setup and connection management.
"""
import logging
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class Center(Base):
    """Database model for storing center information."""
    __tablename__ = "centers"
    
    id = Column(Integer, primary_key=True, index=True)
    center_id = Column(String, unique=True, index=True, nullable=False)
    center_name = Column(String, nullable=False)
    slug = Column(String, index=True, nullable=False)
    zip_code = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, default="USA")
    radius = Column(Integer, default=5)
    owner_email = Column(String, nullable=True)
    location_data = Column(Text, nullable=True)  # JSON string of full location data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class BatchRun(Base):
    """Database model for tracking batch runs."""
    __tablename__ = "batch_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="running")  # running, completed, failed
    total_centers = Column(Integer, default=0)
    processed_centers = Column(Integer, default=0)
    successful_centers = Column(Integer, default=0)
    failed_centers = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Global database engine and session factory
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        database_url = settings.database_url
        
        # For SQLite, use StaticPool to allow multiple threads
        if database_url.startswith("sqlite"):
            _engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=settings.debug
            )
        else:
            _engine = create_engine(database_url, echo=settings.debug)
        
        logger.info(f"Database engine created: {database_url}")
    
    return _engine


def get_session_local():
    """Get or create the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Session factory created")
    
    return _SessionLocal


def init_db():
    """Initialize the database by creating all tables."""
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        raise


def get_db() -> Session:
    """Get a database session."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Get a database session (non-generator version for use in non-FastAPI contexts)."""
    SessionLocal = get_session_local()
    return SessionLocal()

