from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.ai.policy.schemas import (
    PolicyChecks,
    PolicyConfig,
    PolicyDecision,
    PolicyEvaluationRequest,
    PolicyEvaluationResponse,
)


class PolicyEngine:
    """Deterministic, bounded Policy Engine evaluating AI-proposed recovery actions."""

    @staticmethod
    def evaluate(
        request: PolicyEvaluationRequest,
        config: PolicyConfig | dict[str, Any] | None = None,
        policy_id: str | None = None,
    ) -> PolicyEvaluationResponse:
        if config is None:
            resolved_config = PolicyConfig()
        elif isinstance(config, dict):
            resolved_config = PolicyConfig(**config)
        else:
            resolved_config = config

        checks = PolicyChecks()

        # 1. Merchant policy enablement
        if not resolved_config.enabled:
            checks.enabled = False
            return PolicyEvaluationResponse(
                decision=PolicyDecision.DENY,
                reason="Policy is disabled for this merchant.",
                policy_id=policy_id,
                checks=checks,
            )

        # 2. Action type validation against allowed whitelist
        if request.action_type not in resolved_config.allowed_actions:
            checks.action_allowed = False
            return PolicyEvaluationResponse(
                decision=PolicyDecision.DENY,
                reason=f"Action '{request.action_type}' is not permitted by merchant policy.",
                policy_id=policy_id,
                checks=checks,
            )

        # 3. Maximum attempt limit (stopping rule)
        if request.attempt_number >= resolved_config.max_attempts:
            checks.attempt_limit = False
            return PolicyEvaluationResponse(
                decision=PolicyDecision.DENY,
                reason=f"Maximum recovery attempts ({resolved_config.max_attempts}) reached; stopping automated recovery.",
                policy_id=policy_id,
                checks=checks,
            )

        # 4. Cooldown window between attempts
        if request.last_attempt_at is not None and resolved_config.cooldown_minutes > 0:
            now = datetime.now(timezone.utc)
            last_attempt = request.last_attempt_at
            if last_attempt.tzinfo is None:
                last_attempt = last_attempt.replace(tzinfo=timezone.utc)

            elapsed_seconds = (now - last_attempt).total_seconds()
            required_seconds = resolved_config.cooldown_minutes * 60
            if elapsed_seconds < required_seconds:
                remaining_mins = max(1, int((required_seconds - elapsed_seconds) / 60))
                checks.cooldown = False
                return PolicyEvaluationResponse(
                    decision=PolicyDecision.DENY,
                    reason=f"Cooldown active: {remaining_mins} minute(s) remaining before next attempt.",
                    policy_id=policy_id,
                    checks=checks,
                )

        # 5. Risk restriction check (High / Critical risk requires human review)
        if request.risk_level:
            normalized_risk = request.risk_level.strip().upper()
            restricted_levels = [r.strip().upper() for r in resolved_config.risk_restrictions]
            if normalized_risk in restricted_levels:
                checks.risk_acceptable = False
                return PolicyEvaluationResponse(
                    decision=PolicyDecision.REQUIRE_REVIEW,
                    reason=f"Transaction risk level '{request.risk_level}' requires human review before action.",
                    policy_id=policy_id,
                    checks=checks,
                )

        # 6. Minimum recovery probability threshold
        if request.recovery_probability < resolved_config.min_recovery_probability:
            checks.probability_threshold = False
            return PolicyEvaluationResponse(
                decision=PolicyDecision.REQUIRE_REVIEW,
                reason=(
                    f"Recovery probability ({request.recovery_probability:.2f}) is below minimum "
                    f"threshold ({resolved_config.min_recovery_probability:.2f}); requires merchant review."
                ),
                policy_id=policy_id,
                checks=checks,
            )

        # 7. Maximum amount limit for automated actions
        if request.amount > resolved_config.max_recovery_amount:
            checks.amount_limit = False
            return PolicyEvaluationResponse(
                decision=PolicyDecision.REQUIRE_REVIEW,
                reason=(
                    f"Recovery amount (INR {request.amount:,.2f}) exceeds automated threshold "
                    f"(INR {resolved_config.max_recovery_amount:,.2f}); requires human approval."
                ),
                policy_id=policy_id,
                checks=checks,
            )

        # 8. AI confidence threshold
        if request.confidence is not None and request.confidence < resolved_config.min_confidence:
            checks.confidence_acceptable = False
            return PolicyEvaluationResponse(
                decision=PolicyDecision.REQUIRE_REVIEW,
                reason=(
                    f"Proposed action confidence ({request.confidence:.2f}) is below policy threshold "
                    f"({resolved_config.min_confidence:.2f}); manual review recommended."
                ),
                policy_id=policy_id,
                checks=checks,
            )

        # All checks passed
        return PolicyEvaluationResponse(
            decision=PolicyDecision.ALLOW,
            reason="All merchant recovery policies satisfied.",
            policy_id=policy_id,
            checks=checks,
        )
