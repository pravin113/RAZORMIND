from __future__ import annotations

from typing import Any
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.agent.tools.base import ToolDefinition
from app.db.models import FraudEvent, RiskScore, Transaction
from app.services.ml_analysis import get_risk_summary as service_get_risk_summary


def get_risk_score(db: Session, transaction_id: str) -> dict[str, Any]:
    """Retrieve existing Phase 3 ML risk assessment for a transaction."""
    if not transaction_id:
        return {"error": "transaction_id is required."}

    tx = None
    try:
        uuid_val = UUID(transaction_id)
        tx = db.scalar(select(Transaction).where(Transaction.id == uuid_val))
    except (ValueError, TypeError):
        pass

    if tx is None:
        tx = db.scalar(select(Transaction).where(Transaction.razorpay_payment_id == transaction_id))

    lookup_id = tx.id if tx else None
    if lookup_id is None:
        try:
            lookup_id = UUID(transaction_id)
        except (ValueError, TypeError):
            return {"error": f"Transaction '{transaction_id}' not found."}

    risk = db.scalar(
        select(RiskScore)
        .where(RiskScore.transaction_id == lookup_id)
        .order_by(RiskScore.created_at.desc())
    )
    if risk is None:
        return {
            "transaction_id": str(lookup_id),
            "status": "not_scored",
            "message": "No risk score has been evaluated for this transaction.",
        }

    fraud_events = db.scalars(
        select(FraudEvent).where(FraudEvent.transaction_id == lookup_id)
    ).all()
    event_details = [
        {"event_type": ev.event_type, "severity": ev.severity, "reason": ev.reason}
        for ev in fraud_events
    ]

    return {
        "transaction_id": str(lookup_id),
        "risk_score": float(risk.risk_score),
        "fraud_probability": float(risk.fraud_probability),
        "anomaly_score": float(risk.anomaly_score),
        "risk_level": risk.risk_level,
        "model_version": risk.model_version,
        "created_at": risk.created_at.isoformat() if risk.created_at else None,
        "fraud_events": event_details,
    }


def get_risk_summary(db: Session) -> dict[str, Any]:
    """Retrieve an aggregate summary of all evaluated risk scores and fraud distribution."""
    base_summary = service_get_risk_summary(db)

    # Additional fraud/anomaly count breakdowns
    high_count = db.scalar(
        select(func.count(RiskScore.id)).where(RiskScore.risk_level == "HIGH")
    ) or 0
    critical_count = db.scalar(
        select(func.count(RiskScore.id)).where(RiskScore.risk_level == "CRITICAL")
    ) or 0
    fraud_event_count = db.scalar(select(func.count(FraudEvent.id))) or 0

    return {
        "total_transactions_analyzed": base_summary["total_risk_scores"],
        "average_risk_score": base_summary["average_risk_score"],
        "high_risk_count": high_count,
        "critical_risk_count": critical_count,
        "fraud_events_count": fraud_event_count,
        "risk_distribution": base_summary.get("by_risk_level", {}),
    }


tool_get_risk_score = ToolDefinition(
    name="get_risk_score",
    description="Retrieve the ML risk score, fraud probability, anomaly score, and risk level for a transaction.",
    parameters={
        "type": "object",
        "properties": {
            "transaction_id": {
                "type": "string",
                "description": "Unique transaction ID (UUID) or payment ID to check risk score for.",
            }
        },
        "required": ["transaction_id"],
    },
    func=get_risk_score,
)

tool_get_risk_summary = ToolDefinition(
    name="get_risk_summary",
    description="Retrieve high-level risk overview including total transactions analyzed, high/critical risk counts, and risk level distribution.",
    parameters={
        "type": "object",
        "properties": {},
    },
    func=get_risk_summary,
)
