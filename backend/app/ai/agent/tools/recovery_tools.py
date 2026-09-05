from __future__ import annotations

from typing import Any
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.agent.tools.base import ToolDefinition
from app.db.models import RecoveryAction, RecoveryOpportunity, Transaction
from app.services.ml_analysis import get_recovery_summary as service_get_recovery_summary


def get_recovery_probability(db: Session, transaction_id: str) -> dict[str, Any]:
    """Retrieve recovery opportunity details and probability for a transaction."""
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

    opp = db.scalar(
        select(RecoveryOpportunity)
        .where(RecoveryOpportunity.transaction_id == lookup_id)
        .order_by(RecoveryOpportunity.created_at.desc())
    )
    if opp is None:
        return {
            "transaction_id": str(lookup_id),
            "status": "none",
            "message": "No recovery opportunity recorded for this transaction.",
        }

    estimated_recoverable = float(opp.amount_at_risk * opp.recovery_probability)

    return {
        "transaction_id": str(lookup_id),
        "opportunity_id": str(opp.id),
        "recovery_probability": float(opp.recovery_probability),
        "amount_at_risk": float(opp.amount_at_risk),
        "estimated_recoverable_amount": round(estimated_recoverable, 2),
        "priority": opp.priority,
        "status": opp.status,
        "recommendation": opp.recommended_action,
        "created_at": opp.created_at.isoformat() if opp.created_at else None,
    }


def get_recovery_summary(db: Session) -> dict[str, Any]:
    """Retrieve an aggregate summary of failed payment recovery opportunities and expected yields."""
    base_summary = service_get_recovery_summary(db)

    failed_payments_count = db.scalar(
        select(func.count(Transaction.id)).where(Transaction.status == "failed")
    ) or 0

    # Recovered amount from successful actions where recorded
    recovered_count = db.scalar(
        select(func.count(RecoveryOpportunity.id)).where(RecoveryOpportunity.status == "recovered")
    ) or 0

    total_opps = base_summary["total_opportunities"]
    recovery_rate = round(recovered_count / total_opps, 4) if total_opps > 0 else 0.0

    return {
        "failed_payments": failed_payments_count,
        "recovery_opportunities": total_opps,
        "open_opportunities": base_summary["open_opportunities"],
        "average_recovery_probability": round(base_summary["average_recovery_probability"], 4),
        "estimated_recoverable_amount": float(base_summary["expected_recovered_value"]),
        "recovered_opportunities": recovered_count,
        "recovery_rate": recovery_rate,
    }


tool_get_recovery_probability = ToolDefinition(
    name="get_recovery_probability",
    description="Retrieve recovery probability, estimated recoverable amount, and strategy recommendations for a failed transaction.",
    parameters={
        "type": "object",
        "properties": {
            "transaction_id": {
                "type": "string",
                "description": "Unique transaction ID (UUID) or payment ID to check recovery potential for.",
            }
        },
        "required": ["transaction_id"],
    },
    func=get_recovery_probability,
)

tool_get_recovery_summary = ToolDefinition(
    name="get_recovery_summary",
    description="Retrieve aggregate summary of recovery opportunities, expected recoverable revenue, average recovery rate, and open counts.",
    parameters={
        "type": "object",
        "properties": {},
    },
    func=get_recovery_summary,
)


def execute_recovery_workflow(
    db: Session,
    merchant_id: str,
    transaction_id: str | None = None,
    opportunity_id: str | None = None,
) -> dict[str, Any]:
    """Execute bounded autonomous revenue recovery workflow through Policy Engine."""
    from app.ai.workflows.recovery_orchestrator import RevenueRecoveryOrchestrator
    from app.ai.workflows.schemas import WorkflowExecuteRequest

    try:
        m_uuid = UUID(merchant_id)
    except (ValueError, TypeError):
        return {"error": f"Invalid merchant UUID: {merchant_id}"}

    tx_uuid = None
    if transaction_id:
        try:
            tx_uuid = UUID(transaction_id)
        except (ValueError, TypeError):
            pass

    opp_uuid = None
    if opportunity_id:
        try:
            opp_uuid = UUID(opportunity_id)
        except (ValueError, TypeError):
            pass

    req = WorkflowExecuteRequest(
        merchant_id=m_uuid,
        transaction_id=tx_uuid,
        opportunity_id=opp_uuid,
    )
    orchestrator = RevenueRecoveryOrchestrator(db)
    res = orchestrator.execute_recovery(req)
    return {
        "workflow_id": res.workflow_id,
        "status": res.status,
        "proposed_action": res.decision.action,
        "confidence": res.decision.confidence,
        "policy_decision": res.policy.decision,
        "policy_reason": res.policy.reason,
        "execution_status": res.execution.status,
        "verification_status": res.verification.status,
        "amount_recovered": res.amount_recovered,
        "tools_used": res.tools_used,
    }


tool_execute_recovery_workflow = ToolDefinition(
    name="execute_recovery_workflow",
    description="Execute the 9-step bounded autonomous revenue recovery workflow (investigate, propose, policy-check, act in test mode, verify, audit, learn).",
    parameters={
        "type": "object",
        "properties": {
            "merchant_id": {
                "type": "string",
                "description": "Target merchant UUID",
            },
            "transaction_id": {
                "type": "string",
                "description": "Optional transaction UUID to recover",
            },
            "opportunity_id": {
                "type": "string",
                "description": "Optional recovery opportunity UUID",
            },
        },
        "required": ["merchant_id"],
    },
    func=execute_recovery_workflow,
)

