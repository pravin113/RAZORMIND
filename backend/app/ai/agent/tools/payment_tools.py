from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.agent.tools.base import ToolDefinition
from app.db.models import Transaction
from app.services.razorpay_service import RazorpayConfigurationError, RazorpayServiceError, get_razorpay_service


def get_payment_details(db: Session, razorpay_payment_id: str) -> dict[str, Any]:
    """Retrieve safe payment information via the Razorpay service or local transaction record."""
    if not razorpay_payment_id:
        return {"error": "razorpay_payment_id is required."}

    # First attempt to fetch live from Razorpay test API if credentials are configured
    rzp_data: dict[str, Any] | None = None
    try:
        service = get_razorpay_service()
        if service.configured:
            raw_payment = service.fetch_payment(razorpay_payment_id)
            # Sanitize and extract only safe merchant information
            rzp_data = {
                "id": raw_payment.get("id"),
                "entity": raw_payment.get("entity"),
                "amount": raw_payment.get("amount", 0) / 100 if raw_payment.get("amount") else 0.0,
                "currency": raw_payment.get("currency"),
                "status": raw_payment.get("status"),
                "method": raw_payment.get("method"),
                "order_id": raw_payment.get("order_id"),
                "created_at": raw_payment.get("created_at"),
                "error_code": raw_payment.get("error_code"),
                "error_description": raw_payment.get("error_description"),
            }
    except (RazorpayConfigurationError, RazorpayServiceError):
        pass

    if rzp_data:
        return {"source": "razorpay_api", "payment": rzp_data}

    # Fallback to local database transaction if available
    tx = db.scalar(select(Transaction).where(Transaction.razorpay_payment_id == razorpay_payment_id))
    if tx:
        return {
            "source": "database_fallback",
            "payment": {
                "id": tx.razorpay_payment_id,
                "amount": float(tx.amount),
                "currency": tx.currency,
                "status": tx.status,
                "method": tx.payment_method,
                "order_id": tx.razorpay_order_id,
                "timestamp": tx.transaction_timestamp.isoformat() if tx.transaction_timestamp else None,
            },
        }

    return {"error": f"Payment '{razorpay_payment_id}' not found in Razorpay or database."}


tool_get_payment_details = ToolDefinition(
    name="get_payment_details",
    description="Retrieve sanitized details for a Razorpay payment via test API or local transaction fallback without exposing credentials.",
    parameters={
        "type": "object",
        "properties": {
            "razorpay_payment_id": {
                "type": "string",
                "description": "Razorpay payment identifier (e.g. 'pay_12345').",
            }
        },
        "required": ["razorpay_payment_id"],
    },
    func=get_payment_details,
)
