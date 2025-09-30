from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=settings.debug   # Log SQL queries in debug mode
)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create Base class for models
Base = declarative_base()


# Database session dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    Automatically handles session lifecycle and cleanup.
    
    Usage in FastAPI endpoints:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# Event listeners for connection pool
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Set database-specific configuration on connection.
    Currently empty but can be used for PostgreSQL settings.
    """
    pass


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """
    Called when connection is returned to the pool.
    Can be used for cleanup or logging.
    """
    pass


def init_db():
    """
    Initialize database by creating all tables.
    Should be called on application startup.
    """
    try:
        # Import all models here to ensure they are registered with Base
        from models import ticket, interaction, conversation, media
        
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def check_db_connection() -> bool:
    """
    Check if database connection is working.
    Returns True if connection successful, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_db_session() -> Session:
    """
    Get a database session for use outside of FastAPI dependency injection.
    Useful for scripts, background tasks, etc.
    
    Remember to close the session when done:
        db = get_db_session()
        try:
            # do work
        finally:
            db.close()
    """
    return SessionLocal()


# Database health check
def health_check() -> dict:
    """
    Perform database health check.
    Returns status information.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT version()")
            version = result.fetchone()[0]
            
        return {
            "status": "healthy",
            "database": "postgresql",
            "version": version,
            "pool_size": engine.pool.size(),
            "pool_checked_out": engine.pool.checkedout()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }