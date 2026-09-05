from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import create_database_engine


def check_database_health() -> dict[str, object]:
    if not settings.database_url:
        return {
            "status": "not_configured",
            "configured": False,
            "database": "unavailable",
        }

    try:
        engine = create_database_engine(settings.database_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return {
            "status": "unhealthy",
            "configured": True,
            "database": "unreachable",
        }

    return {
        "status": "ok",
        "configured": True,
        "database": "reachable",
    }

