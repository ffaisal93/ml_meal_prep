"""
Database setup and session management
Supports both PostgreSQL (via DATABASE_URL) and SQLite (with persistent volume)
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional
import os
from app.config import settings

# Determine database URL
# Railway provides DATABASE_URL for PostgreSQL, or use SQLite with persistent volume
database_url = os.getenv("DATABASE_URL") or settings.database_url

if database_url:
    # Use PostgreSQL (Railway's managed database)
    # Railway provides DATABASE_URL in format: postgres://user:pass@host:port/dbname
    # SQLAlchemy needs: postgresql+psycopg2://user:pass@host:port/dbname
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif not database_url.startswith("postgresql"):
        database_url = f"postgresql+psycopg2://{database_url}"
    
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,  # Connection pool size
        max_overflow=10,
        echo=False
    )
else:
    # Use SQLite with persistent volume path if available
    persistent_volume_path = os.getenv("PERSISTENT_VOLUME_PATH") or settings.persistent_volume_path
    if persistent_volume_path:
        DB_PATH = os.path.join(persistent_volume_path, settings.db_path)
    else:
        DB_PATH = settings.db_path
    
    # Ensure directory exists
    db_dir = os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else "."
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},  # Needed for SQLite
        echo=False  # Set to True for SQL query logging
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Export SessionLocal for use in main.py
__all__ = ['Base', 'SessionLocal', 'UserPreference', 'init_db', 'get_db', 'get_user_preferences', 'save_user_preference']

# Base class for models
Base = declarative_base()


class UserPreference(Base):
    """User preference and meal plan history"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    query = Column(Text, nullable=False)
    dietary_restrictions = Column(JSON, nullable=True)
    preferences = Column(JSON, nullable=True)
    special_requirements = Column(JSON, nullable=True)
    meal_plan_id = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, meal_plan_id={self.meal_plan_id})>"


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_preferences(db: Session, user_id: str, limit: int = 10):
    """Get recent preferences for a user"""
    return db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).order_by(
        UserPreference.created_at.desc()
    ).limit(limit).all()


def save_user_preference(
    db: Session,
    user_id: str,
    query: str,
    meal_plan_id: Optional[str] = None,
    dietary_restrictions: Optional[dict] = None,
    preferences: Optional[dict] = None,
    special_requirements: Optional[dict] = None
) -> UserPreference:
    """Save user preference to database"""
    preference = UserPreference(
        user_id=user_id,
        query=query,
        meal_plan_id=meal_plan_id,
        dietary_restrictions=dietary_restrictions,
        preferences=preferences,
        special_requirements=special_requirements
    )
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference

