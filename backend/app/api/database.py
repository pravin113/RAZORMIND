from fastapi import APIRouter

from app.schemas.database import DatabaseHealth
from app.services.database import check_database_health

router = APIRouter(prefix="/db", tags=["database"])


@router.get("/health", response_model=DatabaseHealth)
async def database_health_check() -> dict[str, object]:
    return check_database_health()

