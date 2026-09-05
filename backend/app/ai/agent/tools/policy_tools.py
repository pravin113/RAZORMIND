from __future__ import annotations

from typing import Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.agent.tools.base import ToolDefinition
from app.db.models import Policy


def get_policy(db: Session, merchant_id: str | None = None) -> dict[str, Any]:
    """Retrieve safety rules and configured policies governing autonomous actions."""
    configured_policies = []
    if merchant_id:
        try:
            m_uuid = UUID(merchant_id)
            policies = db.scalars(
                select(Policy).where(Policy.merchant_id == m_uuid, Policy.enabled.is_(True))
            ).all()
            configured_policies = [
                {
                    "policy_name": p.policy_name,
                    "policy_type": p.policy_type,
                    "configuration": p.configuration,
                }
                for p in policies
            ]
        except (ValueError, TypeError):
            pass

    # Standard Phase 5 read-only safety guardrails
    safe_defaults = {
        "automatic_refunds": False,
        "automatic_payment_retries": False,
        "account_blocking": False,
        "destructive_actions_allowed": False,
        "mode": "read_only_intelligence",
        "description": "In Phase 5, all tools and operations are strictly read-only. Financial action execution is deferred to Phase 6 Policy Engine.",
    }

    return {
        "status": "enforced",
        "guardrails": safe_defaults,
        "configured_merchant_policies": configured_policies,
    }


def evaluate_recovery_policy(
    db: Session,
    merchant_id: str,
    action_type: str,
    amount: float,
    recovery_probability: float,
    attempt_number: int = 1,
    risk_level: str | None = None,
) -> dict[str, Any]:
    """Evaluate whether an autonomous recovery action satisfies merchant policy."""
    from app.ai.policy.schemas import PolicyEvaluationRequest
    from app.ai.policy.service import evaluate_merchant_policy as service_eval_policy

    try:
        m_uuid = UUID(merchant_id)
    except (ValueError, TypeError):
        return {"error": f"Invalid merchant UUID: {merchant_id}"}

    req = PolicyEvaluationRequest(
        merchant_id=m_uuid,
        action_type=action_type,
        amount=amount,
        recovery_probability=recovery_probability,
        attempt_number=attempt_number,
        risk_level=risk_level,
    )
    res = service_eval_policy(db, req)
    return {
        "decision": res.decision.value,
        "reason": res.reason,
        "policy_id": res.policy_id,
        "checks": res.checks.model_dump(),
    }


tool_get_policy = ToolDefinition(
    name="get_policy",
    description="Retrieve merchant safety policy and system guardrails (confirms read-only mode; prohibits automatic refunds, retries, or blocking).",
    parameters={
        "type": "object",
        "properties": {
            "merchant_id": {
                "type": "string",
                "description": "Optional merchant UUID to check specific configured policies for.",
            }
        },
    },
    func=get_policy,
)

tool_evaluate_recovery_policy = ToolDefinition(
    name="evaluate_recovery_policy",
    description="Evaluate whether a proposed recovery action (e.g. retry_payment) is permitted by merchant policy (returns ALLOW, DENY, or REQUIRE_REVIEW).",
    parameters={
        "type": "object",
        "properties": {
            "merchant_id": {
                "type": "string",
                "description": "Target merchant UUID",
            },
            "action_type": {
                "type": "string",
                "description": "Action type to evaluate (e.g. retry_payment, send_payment_reminder)",
            },
            "amount": {
                "type": "number",
                "description": "Amount involved in recovery (INR)",
            },
            "recovery_probability": {
                "type": "number",
                "description": "Estimated recovery probability (0.0 to 1.0)",
            },
            "attempt_number": {
                "type": "integer",
                "description": "Current attempt count",
            },
            "risk_level": {
                "type": "string",
                "description": "Transaction risk level (LOW, MEDIUM, HIGH, CRITICAL)",
            },
        },
        "required": ["merchant_id", "action_type", "amount", "recovery_probability"],
    },
    func=evaluate_recovery_policy,
)
