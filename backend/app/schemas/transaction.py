from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.common import ORMModel


class TransactionCreate(ORMModel):
    merchant_id: UUID
    customer_id: UUID | None = None
    razorpay_payment_id: str | None = None
    razorpay_order_id: str | None = None
    amount: Decimal
    currency: str = "INR"
    status: str
    payment_method: str
    transaction_timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class TransactionRead(ORMModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    merchant_id: UUID
    customer_id: UUID | None
    razorpay_payment_id: str | None
    razorpay_order_id: str | None
    amount: Decimal
    currency: str
    status: str
    payment_method: str
    transaction_timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    created_at: datetime

