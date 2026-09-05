from datetime import datetime
from uuid import UUID

from app.schemas.common import ORMModel


class MerchantCreate(ORMModel):
    name: str
    email: str
    business_type: str
    currency: str = "INR"


class MerchantRead(MerchantCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

