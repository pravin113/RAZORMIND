from __future__ import annotations

from typing import Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.agent.tools.base import ToolDefinition
from app.db.models import PaymentAttempt, Transaction


def get_transaction(db: Session, transaction_id: str) -> dict[str, Any]:
    """Retrieve non-sensitive details for a specific transaction by ID."""
    if not transaction_id:
        return {"error": "transaction_id is required."}

    # Support UUID or razorpay_payment_id query
    tx = None
    try:
        uuid_val = UUID(transaction_id)
        tx = db.scalar(select(Transaction).where(Transaction.id == uuid_val))
    except (ValueError, TypeError):
        pass

    if tx is None:
        tx = db.scalar(select(Transaction).where(Transaction.razorpay_payment_id == transaction_id))

    if tx is None:
        return {"error": f"Transaction '{transaction_id}' not found."}

    failure_reason = None
    if tx.status == "failed":
        attempt = db.scalar(
            select(PaymentAttempt)
            .where(PaymentAttempt.transaction_id == tx.id, PaymentAttempt.status == "failed")
            .order_by(PaymentAttempt.attempted_at.desc())
        )
        if attempt:
            failure_reason = attempt.failure_reason or attempt.failure_code

    return {
        "transaction_id": str(tx.id),
        "razorpay_payment_id": tx.razorpay_payment_id,
        "amount": float(tx.amount),
        "currency": tx.currency,
        "status": tx.status,
        "payment_method": tx.payment_method,
        "transaction_timestamp": tx.transaction_timestamp.isoformat() if tx.transaction_timestamp else None,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
        "failure_reason": failure_reason,
    }


tool_get_transaction = ToolDefinition(
    name="get_transaction",
    description="Retrieve non-sensitive details for a specific transaction including status, amount, payment method, and failure reason if failed.",
    parameters={
        "type": "object",
        "properties": {
            "transaction_id": {
                "type": "string",
                "description": "Unique transaction ID (UUID) or Razorpay payment ID.",
            }
        },
        "required": ["transaction_id"],
    },
    func=get_transaction,
)
