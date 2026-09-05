from typing import Any

from pydantic import BaseModel, Field


class RazorpayOrderCreate(BaseModel):
    amount: int = Field(gt=0)
    currency: str = "INR"
    receipt: str | None = None
    notes: dict[str, Any] | None = None


class RazorpayOrderResponse(BaseModel):
    id: str
    entity: str | None = None
    amount: int
    amount_paid: int | None = None
    amount_due: int | None = None
    currency: str
    receipt: str | None = None
    status: str | None = None
    attempts: int | None = None
    notes: dict[str, Any] | list[Any] | None = None
    created_at: int | None = None


class RazorpayPaymentResponse(BaseModel):
    id: str
    entity: str | None = None
    amount: int
    currency: str
    status: str | None = None
    order_id: str | None = None
    method: str | None = None
    captured: bool | None = None
    description: str | None = None
    email: str | None = None
    contact: str | None = None
    error_code: str | None = None
    error_description: str | None = None
    created_at: int | None = None
    notes: dict[str, Any] | list[Any] | None = None


class RazorpayPaymentsResponse(BaseModel):
    count: int
    items: list[RazorpayPaymentResponse]


class RazorpayStatusResponse(BaseModel):
    configured: bool
    mode: str = "test"


class WebhookResponse(BaseModel):
    status: str
    event_id: str | None = None
    event_type: str | None = None
    processed: bool

