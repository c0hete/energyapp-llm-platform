from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import get_settings


class Base(DeclarativeBase):
    """Base declarativa para modelos ORM."""


def _create_engine():
    settings = get_settings()
    connect_args = {}
    if settings.db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(settings.db_url, echo=False, future=True, connect_args=connect_args)


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope():
    """Context manager para sesiones; hace commit/rollback segun resultado."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
