from __future__ import annotations

from typing import Any
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.agent.tools.base import ToolDefinition
from app.db.models import Customer, RecoveryOpportunity, Transaction


def get_customer_history(db: Session, customer_id: str) -> dict[str, Any]:
    """Retrieve aggregate payment and recovery history for a customer."""
    if not customer_id:
        return {"error": "customer_id is required."}

    customer = None
    try:
        uuid_val = UUID(customer_id)
        customer = db.scalar(select(Customer).where(Customer.id == uuid_val))
    except (ValueError, TypeError):
        pass

    if customer is None:
        customer = db.scalar(select(Customer).where(Customer.external_customer_id == customer_id))

    if customer is None:
        return {"error": f"Customer '{customer_id}' not found."}

    # Aggregate transactions
    tx_query = select(
        func.count(Transaction.id).label("total_tx"),
        func.sum(Transaction.amount).label("total_amount"),
    ).where(Transaction.customer_id == customer.id)
    tx_stats = db.execute(tx_query).first()
    total_tx = tx_stats.total_tx if tx_stats else 0
    total_amount = float(tx_stats.total_amount) if tx_stats and tx_stats.total_amount else 0.0

    # Successful vs failed
    success_count = db.scalar(
        select(func.count(Transaction.id)).where(
            Transaction.customer_id == customer.id,
            Transaction.status.in_(["captured", "paid", "authorized"]),
        )
    ) or 0

    failed_count = db.scalar(
        select(func.count(Transaction.id)).where(
            Transaction.customer_id == customer.id,
            Transaction.status == "failed",
        )
    ) or 0

    # Recovery opportunities for this customer
    recoveries = db.scalars(
        select(RecoveryOpportunity).where(RecoveryOpportunity.customer_id == customer.id)
    ).all()
    recovery_history = [
        {
            "opportunity_id": str(rec.id),
            "amount_at_risk": float(rec.amount_at_risk),
            "recovery_probability": float(rec.recovery_probability),
            "status": rec.status,
            "priority": rec.priority,
        }
        for rec in recoveries
    ]

    return {
        "customer_id": str(customer.id),
        "external_customer_id": customer.external_customer_id,
        "transaction_count": total_tx,
        "successful_payments": success_count,
        "failed_payments": failed_count,
        "total_amount": total_amount,
        "recovery_history": recovery_history,
        "recent_payment_behavior": "frequent_failures" if failed_count > success_count else "healthy",
    }


tool_get_customer_history = ToolDefinition(
    name="get_customer_history",
    description="Retrieve aggregated non-PII payment history for a customer including transaction count, successes, failures, total spent, and recovery history.",
    parameters={
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Internal customer UUID or external customer ID.",
            }
        },
        "required": ["customer_id"],
    },
    func=get_customer_history,
)
