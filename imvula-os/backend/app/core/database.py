from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Every table in the database is built from this base."""
    pass


_connect_args = {}
if settings.sqlalchemy_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(settings.sqlalchemy_url, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Give each request its own database session, then close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
