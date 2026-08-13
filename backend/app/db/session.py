from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import Generator

from app.core.config import settings

# SQLAlchemy 2.0 DeclarativeBase class
class Base(DeclarativeBase):
    pass

# Create Engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# SessionLocal Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# FastAPI Dependency for database sessions
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
