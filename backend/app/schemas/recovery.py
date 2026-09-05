from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.schemas.common import ORMModel


class RecoveryOpportunityCreate(ORMModel):
    transaction_id: UUID | None = None
    customer_id: UUID | None = None
    opportunity_type: str
    amount_at_risk: Decimal
    recovery_probability: Decimal
    priority: str
    status: str
    recommended_action: str
    expires_at: datetime | None = None


class RecoveryOpportunityRead(RecoveryOpportunityCreate):
    id: UUID
    created_at: datetime

