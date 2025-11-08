from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency function for FastAPI
def get_db():
    """
    FastAPI dependency that provides a database session.
    It automatically opens a session for each request and closes it afterward.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()