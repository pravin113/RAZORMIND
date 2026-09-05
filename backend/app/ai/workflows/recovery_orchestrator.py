from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.policy.engine import PolicyEngine
from app.ai.policy.schemas import PolicyDecision, PolicyEvaluationRequest
from app.ai.policy.service import get_merchant_policy
from app.ai.rag.service import get_rag_context_for_prompt
from app.ai.workflows.schemas import (
    ProposedDecision,
    RecoveryOutcomeRead,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse,
    WorkflowExecutionResult,
    WorkflowPolicyResult,
    WorkflowVerificationResult,
)
from app.db.models import (
    AgentDecision,
    AuditLog,
    Customer,
    Merchant,
    PaymentAttempt,
    RecoveryAction,
    RecoveryOpportunity,
    RecoveryOutcome,
    RiskScore,
    Transaction,
    utc_now,
)

logger = logging.getLogger(__name__)


class RevenueRecoveryOrchestrator:
    """Bounded, autonomous Revenue Recovery workflow engine.

    Executes:
    OBSERVE -> DETECT -> INVESTIGATE -> DECIDE -> POLICY CHECK -> ACT -> VERIFY -> AUDIT -> LEARN
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def execute_recovery(self, request: WorkflowExecuteRequest) -> WorkflowExecuteResponse:
        workflow_id = str(uuid4())
        tools_used: list[str] = []

        # =========================================================================
        # STEP 1: OBSERVE
        # =========================================================================
        merchant = self.db.get(Merchant, request.merchant_id)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Merchant {request.merchant_id} not found",
            )

        opportunity: RecoveryOpportunity | None = None
        transaction: Transaction | None = None

        if request.opportunity_id:
            opportunity = self.db.get(RecoveryOpportunity, request.opportunity_id)
            if not opportunity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Recovery opportunity {request.opportunity_id} not found",
                )
            if opportunity.transaction_id:
                transaction = self.db.get(Transaction, opportunity.transaction_id)
            tools_used.append("get_recovery_summary")

        if not transaction and request.transaction_id:
            transaction = self.db.get(Transaction, request.transaction_id)
            if not transaction:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Transaction {request.transaction_id} not found",
                )
            tools_used.append("get_transaction")

        # If neither provided, observe most recent failed transaction for merchant
        if not transaction:
            stmt = (
                select(Transaction)
                .where(
                    Transaction.merchant_id == request.merchant_id,
                    Transaction.status.in_(["failed", "requires_payment_method"]),
                )
                .order_by(Transaction.transaction_timestamp.desc())
            )
            transaction = self.db.scalars(stmt).first()
            if not transaction:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No failed transactions found to recover for merchant",
                )
            tools_used.append("get_failed_payments")

        # Observe customer, attempts, risk
        customer: Customer | None = None
        if transaction.customer_id:
            customer = self.db.get(Customer, transaction.customer_id)
            tools_used.append("get_customer_history")

        prior_attempts = list(transaction.payment_attempts)
        attempt_count = len(prior_attempts)
        last_attempt_at = prior_attempts[-1].attempted_at if prior_attempts else None

        # =========================================================================
        # STEP 2: DETECT
        # =========================================================================
        if not opportunity:
            # Check if an existing opportunity references this transaction
            stmt = select(RecoveryOpportunity).where(
                RecoveryOpportunity.transaction_id == transaction.id
            )
            opportunity = self.db.scalars(stmt).first()

        if not opportunity:
            # Detect revenue at risk and initialize recovery opportunity
            # Standard heuristic / baseline probability derived from payment method & amount
            base_prob = Decimal("0.82") if transaction.amount <= Decimal("10000.00") else Decimal("0.60")
            priority = "HIGH" if transaction.amount >= Decimal("5000.00") else "MEDIUM"
            opportunity = RecoveryOpportunity(
                transaction_id=transaction.id,
                customer_id=customer.id if customer else None,
                opportunity_type="automated_retry",
                amount_at_risk=transaction.amount,
                recovery_probability=base_prob,
                priority=priority,
                status="DETECTED",
                recommended_action="retry_payment",
            )
            self.db.add(opportunity)
            self.db.flush()
            tools_used.append("get_recovery_probability")

        recovery_prob = float(opportunity.recovery_probability)

        # =========================================================================
        # STEP 3: INVESTIGATE
        # =========================================================================
        # Check risk scores
        stmt = (
            select(RiskScore)
            .where(RiskScore.transaction_id == transaction.id)
            .order_by(RiskScore.created_at.desc())
        )
        risk_score_rec = self.db.scalars(stmt).first()
        risk_level = risk_score_rec.risk_level.upper() if risk_score_rec else "LOW"
        tools_used.append("get_risk_score")

        # Investigate merchant RAG knowledge
        rag_context = get_rag_context_for_prompt(
            self.db,
            query="payment retry recovery policy rules",
            merchant_id=request.merchant_id,
            top_k=2,
        )
        if rag_context:
            tools_used.append("get_merchant_policy")

        # =========================================================================
        # STEP 4: DECIDE (Structured AI Decision)
        # =========================================================================
        # Apply structured decision logic
        if risk_level in ["HIGH", "CRITICAL"]:
            decision = ProposedDecision(
                action="escalate_to_human",
                confidence=0.95,
                reason=f"Transaction risk level is {risk_level}. Automated recovery suppressed to prevent fraud.",
                expected_recovery=0.0,
            )
        elif attempt_count >= 2:
            decision = ProposedDecision(
                action="escalate_to_human",
                confidence=0.90,
                reason=f"Maximum automated attempts ({attempt_count}) reached. Escalate to merchant support.",
                expected_recovery=0.0,
            )
        elif recovery_prob < 0.65:
            if recovery_prob >= 0.40:
                decision = ProposedDecision(
                    action="send_payment_reminder",
                    confidence=0.75,
                    reason=f"Recovery probability ({recovery_prob:.2f}) below retry threshold; payment reminder proposed.",
                    expected_recovery=float(transaction.amount),
                )
            else:
                decision = ProposedDecision(
                    action="no_action",
                    confidence=0.85,
                    reason=f"Recovery probability ({recovery_prob:.2f}) too low for automated actions.",
                    expected_recovery=0.0,
                )
        else:
            decision = ProposedDecision(
                action="retry_payment",
                confidence=round(recovery_prob, 2),
                reason="Temporary payment failure detected with high recovery probability and acceptable risk.",
                expected_recovery=float(transaction.amount),
            )

        # =========================================================================
        # STEP 5: POLICY CHECK
        # =========================================================================
        merchant_policy = get_merchant_policy(self.db, request.merchant_id, policy_type="recovery")
        eval_request = PolicyEvaluationRequest(
            merchant_id=request.merchant_id,
            action_type=decision.action,
            amount=float(transaction.amount),
            recovery_probability=recovery_prob,
            attempt_number=attempt_count,
            risk_level=risk_level,
            confidence=decision.confidence,
            last_attempt_at=last_attempt_at,
        )

        policy_eval = PolicyEngine.evaluate(
            request=eval_request,
            config=merchant_policy.configuration if merchant_policy else None,
            policy_id=str(merchant_policy.id) if merchant_policy else None,
        )
        tools_used.append("get_policy")

        # =========================================================================
        # STEP 6: ACT (Razorpay TEST MODE)
        # =========================================================================
        exec_status = "blocked"
        exec_details: dict[str, Any] = {}

        if policy_eval.decision == PolicyDecision.ALLOW and not request.dry_run:
            if decision.action == "retry_payment":
                # Simulated Razorpay Test Mode retry
                new_attempt = PaymentAttempt(
                    transaction_id=transaction.id,
                    attempt_number=attempt_count + 1,
                    status="captured",
                    attempted_at=utc_now(),
                )
                self.db.add(new_attempt)

                action_record = RecoveryAction(
                    opportunity_id=opportunity.id,
                    action_type=decision.action,
                    action_status="COMPLETED",
                    attempted_at=utc_now(),
                    completed_at=utc_now(),
                    result={
                        "test_mode": True,
                        "method": transaction.payment_method,
                        "simulated_recovery": True,
                    },
                )
                self.db.add(action_record)
                exec_status = "success"
                exec_details = {"test_mode": True, "action": "retry_payment", "result": "captured"}

            elif decision.action == "send_payment_reminder":
                action_record = RecoveryAction(
                    opportunity_id=opportunity.id,
                    action_type=decision.action,
                    action_status="COMPLETED",
                    attempted_at=utc_now(),
                    completed_at=utc_now(),
                    result={"test_mode": True, "reminder_sent": True, "channel": "email"},
                )
                self.db.add(action_record)
                exec_status = "success"
                exec_details = {"test_mode": True, "action": "send_payment_reminder", "result": "sent"}

            else:
                exec_status = "skipped"
                exec_details = {"action": decision.action, "result": "no_action_needed"}

        else:
            # Action was blocked or dry-run
            if not request.dry_run:
                action_record = RecoveryAction(
                    opportunity_id=opportunity.id,
                    action_type=decision.action,
                    action_status=policy_eval.decision.value,
                    attempted_at=utc_now(),
                    error_message=policy_eval.reason,
                )
                self.db.add(action_record)
            exec_details = {
                "blocked_reason": policy_eval.reason,
                "policy_decision": policy_eval.decision.value,
                "dry_run": request.dry_run,
            }

        # =========================================================================
        # STEP 7: VERIFY
        # =========================================================================
        amount_recovered = 0.0
        verification_status = "pending"

        if exec_status == "success" and decision.action == "retry_payment":
            verification_status = "recovered"
            amount_recovered = float(transaction.amount)
            opportunity.status = "RECOVERED"
            transaction.status = "captured"
        elif policy_eval.decision == PolicyDecision.REQUIRE_REVIEW:
            verification_status = "queued_for_review"
            opportunity.status = "PENDING_REVIEW"
        elif policy_eval.decision == PolicyDecision.DENY:
            verification_status = "stopped"
            opportunity.status = "STOPPED"
        else:
            verification_status = "completed"

        # =========================================================================
        # STEP 8: AUDIT
        # =========================================================================
        if not request.dry_run:
            agent_decision = AgentDecision(
                merchant_id=request.merchant_id,
                transaction_id=transaction.id,
                opportunity_id=opportunity.id,
                decision_type="autonomous_recovery",
                reasoning=decision.reason,
                recommended_action=decision.action,
                confidence=Decimal(str(round(decision.confidence, 4))),
                policy_result=policy_eval.model_dump(),
            )
            self.db.add(agent_decision)

            audit_log = AuditLog(
                merchant_id=request.merchant_id,
                actor_type="autonomous_recovery_agent",
                actor_id="razormind-recovery-v1",
                action="execute_recovery",
                resource_type="recovery_opportunity",
                resource_id=str(opportunity.id),
                decision=policy_eval.decision.value,
                reason=policy_eval.reason,
                metadata_={
                    "workflow_id": workflow_id,
                    "amount_recovered": amount_recovered,
                    "verification": verification_status,
                },
            )
            self.db.add(audit_log)

        # =========================================================================
        # STEP 9: LEARN (Outcome Tracking)
        # =========================================================================
        outcome_id: str | None = None
        if not request.dry_run:
            is_correct = (
                (verification_status == "recovered")
                if policy_eval.decision == PolicyDecision.ALLOW
                else None
            )

            outcome = RecoveryOutcome(
                opportunity_id=opportunity.id,
                merchant_id=request.merchant_id,
                predicted_probability=Decimal(str(round(recovery_prob, 4))),
                chosen_action=decision.action,
                policy_decision=policy_eval.decision.value,
                actual_result=verification_status,
                recovered_amount=Decimal(str(round(amount_recovered, 2))),
                attempt_number=attempt_count + 1,
                prediction_correctness=is_correct,
                metadata_={
                    "workflow_id": workflow_id,
                    "policy_id": policy_eval.policy_id,
                    "tools_used": list(set(tools_used)),
                },
            )
            self.db.add(outcome)
            self.db.commit()
            self.db.refresh(outcome)
            outcome_id = str(outcome.id)
        else:
            self.db.rollback()

        return WorkflowExecuteResponse(
            workflow_id=workflow_id,
            status="completed",
            merchant_id=str(request.merchant_id),
            transaction_id=str(transaction.id),
            opportunity_id=str(opportunity.id),
            decision=decision,
            policy=WorkflowPolicyResult(
                decision=policy_eval.decision.value,
                reason=policy_eval.reason,
                policy_id=policy_eval.policy_id,
                checks=policy_eval.checks.model_dump(),
            ),
            execution=WorkflowExecutionResult(
                status=exec_status,
                action_type=decision.action,
                details=exec_details,
            ),
            verification=WorkflowVerificationResult(
                status=verification_status,
                details={"amount_recovered": amount_recovered},
            ),
            amount_recovered=amount_recovered,
            tools_used=list(dict.fromkeys(tools_used)),
            outcome_id=outcome_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def get_outcome(self, outcome_id: UUID) -> RecoveryOutcome | None:
        return self.db.get(RecoveryOutcome, outcome_id)

    def list_outcomes(
        self,
        merchant_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[RecoveryOutcome]:
        stmt = select(RecoveryOutcome)
        if merchant_id:
            stmt = stmt.where(RecoveryOutcome.merchant_id == merchant_id)
        stmt = stmt.order_by(RecoveryOutcome.created_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())
