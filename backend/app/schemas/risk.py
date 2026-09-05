from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.schemas.common import ORMModel


class RiskScoreCreate(ORMModel):
    transaction_id: UUID
    fraud_probability: Decimal
    anomaly_score: Decimal
    risk_score: Decimal
    risk_level: str
    model_version: str


class RiskScoreRead(RiskScoreCreate):
    id: UUID
    created_at: datetime

