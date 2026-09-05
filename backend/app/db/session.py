from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def get_database_url() -> str:
    url = settings.database_url
    if not url or "user:password@host" in url:
        return "sqlite:///./live_test.db"
    return url


def create_database_engine(database_url: str | None = None):
    url = database_url or get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(
        url,
        pool_pre_ping=settings.database_pool_pre_ping,
        connect_args=connect_args,
    )


engine = None
SessionLocal: sessionmaker[Session] | None = None

if settings.database_url:
    engine = create_database_engine(get_database_url())
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

