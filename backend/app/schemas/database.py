from app.schemas.common import ORMModel


class DatabaseHealth(ORMModel):
    status: str
    configured: bool
    database: str

