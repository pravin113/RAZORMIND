from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.agent.tools.base import ToolDefinition
from app.db.models import PaymentAttempt, RecoveryOpportunity, Transaction


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def get_revenue_metrics(
    db: Session,
    start_date: str | None = None,
    end_date: str | None = None,
    merchant_id: str | None = None,
) -> dict[str, Any]:
    """Calculate merchant revenue, payment success rates, and failure amounts within an optional date window."""
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)

    query = select(Transaction)
    if start_dt:
        query = query.where(Transaction.transaction_timestamp >= start_dt)
    if end_dt:
        query = query.where(Transaction.transaction_timestamp <= end_dt)
    if merchant_id:
        try:
            m_uuid = UUID(merchant_id)
            query = query.where(Transaction.merchant_id == m_uuid)
        except (ValueError, TypeError):
            pass

    transactions = db.scalars(query).all()
    total_count = len(transactions)

    success_statuses = {"captured", "paid", "authorized"}
    successful_txs = [t for t in transactions if t.status in success_statuses]
    failed_txs = [t for t in transactions if t.status == "failed"]

    successful_amount = sum((float(t.amount) for t in successful_txs), 0.0)
    failed_amount = sum((float(t.amount) for t in failed_txs), 0.0)
    total_amount = sum((float(t.amount) for t in transactions), 0.0)

    success_rate = round(len(successful_txs) / total_count, 4) if total_count > 0 else 0.0
    failure_rate = round(len(failed_txs) / total_count, 4) if total_count > 0 else 0.0

    # Recovered metrics in same window if any
    rec_query = select(RecoveryOpportunity).where(RecoveryOpportunity.status == "recovered")
    if start_dt:
        rec_query = rec_query.where(RecoveryOpportunity.created_at >= start_dt)
    if end_dt:
        rec_query = rec_query.where(RecoveryOpportunity.created_at <= end_dt)
    recovered_opps = db.scalars(rec_query).all()
    recovered_amount = sum((float(o.amount_at_risk) for o in recovered_opps), 0.0)
    recovery_rate = round(len(recovered_opps) / len(failed_txs), 4) if failed_txs else 0.0

    return {
        "start_date": start_date,
        "end_date": end_date,
        "transaction_count": total_count,
        "total_revenue": round(successful_amount, 2),
        "successful_payment_amount": round(successful_amount, 2),
        "successful_count": len(successful_txs),
        "failed_payment_amount": round(failed_amount, 2),
        "failed_count": len(failed_txs),
        "payment_success_rate": success_rate,
        "failure_rate": failure_rate,
        "recovered_amount": round(recovered_amount, 2),
        "recovery_rate": recovery_rate,
    }


def get_failed_payments(
    db: Session,
    start_date: str | None = None,
    end_date: str | None = None,
    failure_reason: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Retrieve detailed list of recent failed payment transactions, optionally filtered by reason and date."""
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)

    query = select(Transaction).where(Transaction.status == "failed")
    if start_dt:
        query = query.where(Transaction.transaction_timestamp >= start_dt)
    if end_dt:
        query = query.where(Transaction.transaction_timestamp <= end_dt)

    query = query.order_by(Transaction.transaction_timestamp.desc()).limit(min(limit or 10, 50))
    failed_txs = db.scalars(query).all()

    items = []
    reason_breakdown: dict[str, int] = {}
    for tx in failed_txs:
        attempt = db.scalar(
            select(PaymentAttempt)
            .where(PaymentAttempt.transaction_id == tx.id, PaymentAttempt.status == "failed")
            .order_by(PaymentAttempt.attempted_at.desc())
        )
        reason = (attempt.failure_reason if attempt else None) or (attempt.failure_code if attempt else None) or "unspecified"
        if failure_reason and failure_reason.lower() not in reason.lower():
            continue

        reason_breakdown[reason] = reason_breakdown.get(reason, 0) + 1
        items.append({
            "transaction_id": str(tx.id),
            "razorpay_payment_id": tx.razorpay_payment_id,
            "amount": float(tx.amount),
            "currency": tx.currency,
            "payment_method": tx.payment_method,
            "timestamp": tx.transaction_timestamp.isoformat() if tx.transaction_timestamp else None,
            "failure_reason": reason,
        })

    return {
        "count": len(items),
        "total_failed_amount": round(sum(i["amount"] for i in items), 2),
        "reason_breakdown": reason_breakdown,
        "payments": items,
    }


tool_get_revenue_metrics = ToolDefinition(
    name="get_revenue_metrics",
    description="Calculate aggregate financial metrics including total revenue, successful payment amount, failed amount, success rate, and transaction count over an optional date window.",
    parameters={
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Optional ISO format start date/timestamp (e.g. '2026-09-01').",
            },
            "end_date": {
                "type": "string",
                "description": "Optional ISO format end date/timestamp (e.g. '2026-09-07').",
            },
            "merchant_id": {
                "type": "string",
                "description": "Optional merchant UUID to scope the metrics.",
            },
        },
    },
    func=get_revenue_metrics,
)

tool_get_failed_payments = ToolDefinition(
    name="get_failed_payments",
    description="Retrieve a list and aggregated breakdown of failed payments with amounts, methods, timestamps, and failure causes.",
    parameters={
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Optional start date/timestamp filter.",
            },
            "end_date": {
                "type": "string",
                "description": "Optional end date/timestamp filter.",
            },
            "failure_reason": {
                "type": "string",
                "description": "Optional substring filter on failure reason (e.g. 'card', 'timeout', 'insufficient_funds').",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of failed payment records to return (default 10, max 50).",
            },
        },
    },
    func=get_failed_payments,
)
