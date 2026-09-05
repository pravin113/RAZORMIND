"""
Phase 8 Autonomous Recovery & Policy Engine Hardening Test
Verifies the complete 9-step recovery lifecycle, positive execution,
negative policy stopping rules, outcome persistence, and audit persistence.
"""
from __future__ import annotations

import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

# Ensure backend root is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.ai.policy.schemas import PolicyConfig, PolicyCreate, PolicyDecision
from app.ai.policy.service import create_policy
from app.ai.workflows.recovery_orchestrator import RevenueRecoveryOrchestrator
from app.ai.workflows.schemas import WorkflowExecuteRequest
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
from app.db.session import SessionLocal


def seed_scenario(
    db,
    amount: Decimal = Decimal("2999.00"),
    status: str = "failed",
    risk_level: str = "LOW",
    prior_attempts: int = 0,
    recovery_prob: Decimal = Decimal("0.82"),
) -> tuple[Merchant, Transaction, RecoveryOpportunity]:
    merchant = Merchant(
        name="Phase 8 Test Merchant",
        email=f"phase8_{uuid4().hex[:8]}@example.com",
        business_type="ecommerce",
        currency="INR",
    )
    db.add(merchant)
    db.flush()

    customer = Customer(
        merchant_id=merchant.id,
        external_customer_id=f"cust_{uuid4().hex[:6]}",
        name="Phase 8 Customer",
        email="customer@example.com",
    )
    db.add(customer)
    db.flush()

    tx = Transaction(
        merchant_id=merchant.id,
        customer_id=customer.id,
        amount=amount,
        currency="INR",
        status=status,
        payment_method="card",
        transaction_timestamp=utc_now(),
        metadata_={},
    )
    db.add(tx)
    db.flush()

    risk = RiskScore(
        transaction_id=tx.id,
        fraud_probability=Decimal("0.05") if risk_level == "LOW" else Decimal("0.85"),
        anomaly_score=Decimal("0.10"),
        risk_score=Decimal("0.10") if risk_level == "LOW" else Decimal("0.88"),
        risk_level=risk_level,
        model_version="v1.0.0",
        created_at=utc_now(),
    )
    db.add(risk)

    for i in range(prior_attempts):
        db.add(
            PaymentAttempt(
                transaction_id=tx.id,
                attempt_number=i + 1,
                status="failed",
                failure_code="insufficient_funds",
                attempted_at=utc_now() - timedelta(hours=2 * (prior_attempts - i)),
            )
        )

    opp = RecoveryOpportunity(
        transaction_id=tx.id,
        customer_id=customer.id,
        opportunity_type="automated_retry",
        amount_at_risk=amount,
        recovery_probability=recovery_prob,
        priority="HIGH" if amount >= Decimal("5000.00") else "MEDIUM",
        status="DETECTED",
        recommended_action="retry_payment",
        created_at=utc_now(),
    )
    db.add(opp)
    db.commit()
    return merchant, tx, opp


def run_tests() -> None:
    db = SessionLocal()
    orchestrator = RevenueRecoveryOrchestrator(db)

    print("=" * 60)
    print("PHASE 8: VERIFYING CONTROLLED RECOVERY SCENARIOS")
    print("=" * 60)

    # -------------------------------------------------------------
    # 1. POSITIVE CONTROLLED SCENARIO
    # -------------------------------------------------------------
    print("\n[TEST 1] POSITIVE SCENARIO: ₹2,999 | LOW Risk | Prob 0.82 | Attempt 0")
    merchant, tx, opp = seed_scenario(
        db,
        amount=Decimal("2999.00"),
        status="failed",
        risk_level="LOW",
        prior_attempts=0,
        recovery_prob=Decimal("0.82"),
    )

    create_policy(
        db,
        PolicyCreate(
            merchant_id=merchant.id,
            policy_name="Recovery Rules",
            policy_type="recovery",
            configuration=PolicyConfig(
                enabled=True,
                min_recovery_probability=0.65,
                max_recovery_amount=10000.0,
                max_attempts=2,
                cooldown_minutes=60,
                allowed_actions=["retry_payment", "send_payment_reminder"],
            ),
        ),
    )

    res = orchestrator.execute_recovery(
        WorkflowExecuteRequest(
            merchant_id=merchant.id,
            transaction_id=tx.id,
            opportunity_id=opp.id,
        )
    )

    assert res.status == "completed", f"Expected completed, got {res.status}"
    assert res.decision.action == "retry_payment", f"Expected retry_payment, got {res.decision.action}"
    assert res.policy.decision == PolicyDecision.ALLOW, f"Expected ALLOW, got {res.policy.decision}"
    assert res.execution.status == "success", f"Expected success, got {res.execution.status}"
    assert res.verification.status == "recovered", f"Expected recovered, got {res.verification.status}"
    assert res.amount_recovered == 2999.0, f"Expected 2999.0, got {res.amount_recovered}"
    assert res.outcome_id is not None, "Expected outcome_id to be populated"
    print("  -> Execution: SUCCESS")
    print("  -> Policy Verdict: ALLOW")
    print(f"  -> Amount Recovered: ₹{res.amount_recovered:,.2f}")
    print(f"  -> Tools Used: {res.tools_used}")

    # Verify Database Persistence
    outcome = orchestrator.get_outcome(res.outcome_id)
    assert outcome is not None, "RecoveryOutcome not persisted"
    assert outcome.actual_result == "recovered"
    assert outcome.recovered_amount == Decimal("2999.00")
    assert outcome.prediction_correctness is True

    agent_decision = db.query(AgentDecision).filter(AgentDecision.opportunity_id == opp.id).first()
    assert agent_decision is not None, "AgentDecision not persisted"
    assert agent_decision.recommended_action == "retry_payment"

    audit_log = db.query(AuditLog).filter(AuditLog.resource_id == str(opp.id)).first()
    assert audit_log is not None, "AuditLog not persisted"
    assert audit_log.decision == "ALLOW"
    assert audit_log.actor_type == "autonomous_recovery_agent"

    recovery_action = db.query(RecoveryAction).filter(RecoveryAction.opportunity_id == opp.id).first()
    assert recovery_action is not None, "RecoveryAction not persisted"
    assert recovery_action.action_status == "COMPLETED"
    print("  -> DB Persistence Verified: RecoveryOutcome, AgentDecision, AuditLog, RecoveryAction")

    # -------------------------------------------------------------
    # 2. NEGATIVE CASE A: HIGH RISK
    # -------------------------------------------------------------
    print("\n[TEST 2] NEGATIVE CASE A: High Risk Flagged Transaction")
    merchant_a, tx_a, opp_a = seed_scenario(
        db,
        amount=Decimal("2999.00"),
        risk_level="HIGH",
        recovery_prob=Decimal("0.85"),
    )
    res_a = orchestrator.execute_recovery(
        WorkflowExecuteRequest(merchant_id=merchant_a.id, transaction_id=tx_a.id)
    )
    assert res_a.decision.action == "escalate_to_human"
    assert res_a.policy.decision in ["REQUIRE_REVIEW", "DENY", PolicyDecision.REQUIRE_REVIEW, PolicyDecision.DENY]
    assert res_a.execution.status == "blocked"
    assert res_a.amount_recovered == 0.0
    print("  -> AI Proposed: escalate_to_human")
    print(f"  -> Policy Verdict: {res_a.policy.decision}")
    print("  -> Execution: BLOCKED (No unauthorized funds debited)")

    # -------------------------------------------------------------
    # 3. NEGATIVE CASE B: RECOVERY PROBABILITY BELOW THRESHOLD
    # -------------------------------------------------------------
    print("\n[TEST 3] NEGATIVE CASE B: Recovery Probability (0.45) < 0.65")
    merchant_b, tx_b, opp_b = seed_scenario(
        db,
        amount=Decimal("1500.00"),
        risk_level="LOW",
        recovery_prob=Decimal("0.45"),
    )
    create_policy(
        db,
        PolicyCreate(
            merchant_id=merchant_b.id,
            policy_name="Strict Threshold",
            configuration=PolicyConfig(min_recovery_probability=0.65),
        ),
    )
    res_b = orchestrator.execute_recovery(
        WorkflowExecuteRequest(merchant_id=merchant_b.id, transaction_id=tx_b.id)
    )
    assert res_b.policy.decision in ["REQUIRE_REVIEW", PolicyDecision.REQUIRE_REVIEW]
    assert res_b.execution.status == "blocked"
    assert res_b.amount_recovered == 0.0
    print(f"  -> Policy Verdict: {res_b.policy.decision}")
    print(f"  -> Reason: {res_b.policy.reason}")
    print("  -> Execution: BLOCKED")

    # -------------------------------------------------------------
    # 4. NEGATIVE CASE C: AMOUNT EXCEEDS MAXIMUM
    # -------------------------------------------------------------
    print("\n[TEST 4] NEGATIVE CASE C: Amount (₹25,000) > Maximum (₹10,000)")
    merchant_c, tx_c, opp_c = seed_scenario(
        db,
        amount=Decimal("25000.00"),
        risk_level="LOW",
        recovery_prob=Decimal("0.80"),
    )
    create_policy(
        db,
        PolicyCreate(
            merchant_id=merchant_c.id,
            policy_name="Amount Limit",
            configuration=PolicyConfig(max_recovery_amount=10000.0),
        ),
    )
    res_c = orchestrator.execute_recovery(
        WorkflowExecuteRequest(merchant_id=merchant_c.id, transaction_id=tx_c.id)
    )
    assert res_c.policy.decision in ["REQUIRE_REVIEW", PolicyDecision.REQUIRE_REVIEW]
    assert res_c.execution.status == "blocked"
    assert res_c.amount_recovered == 0.0
    print(f"  -> Policy Verdict: {res_c.policy.decision}")
    print(f"  -> Reason: {res_c.policy.reason}")
    print("  -> Execution: BLOCKED")

    # -------------------------------------------------------------
    # 5. NEGATIVE CASE D: MAXIMUM ATTEMPTS REACHED
    # -------------------------------------------------------------
    print("\n[TEST 5] NEGATIVE CASE D: Prior Attempts (2) >= Max Allowed (2)")
    merchant_d, tx_d, opp_d = seed_scenario(
        db,
        amount=Decimal("3000.00"),
        risk_level="LOW",
        prior_attempts=2,
        recovery_prob=Decimal("0.85"),
    )
    create_policy(
        db,
        PolicyCreate(
            merchant_id=merchant_d.id,
            policy_name="Max Attempts Limit",
            configuration=PolicyConfig(max_attempts=2),
        ),
    )
    res_d = orchestrator.execute_recovery(
        WorkflowExecuteRequest(merchant_id=merchant_d.id, transaction_id=tx_d.id)
    )
    assert res_d.policy.decision in ["DENY", PolicyDecision.DENY]
    assert res_d.execution.status == "blocked"
    assert res_d.verification.status == "stopped"
    assert res_d.amount_recovered == 0.0
    print(f"  -> Policy Verdict: {res_d.policy.decision}")
    print(f"  -> Reason: {res_d.policy.reason}")
    print("  -> Execution: BLOCKED / STOPPED")

    # -------------------------------------------------------------
    # 6. NEGATIVE CASE E: COOLDOWN ACTIVE
    # -------------------------------------------------------------
    print("\n[TEST 6] NEGATIVE CASE E: Cooldown Active (Attempted 10 mins ago, Cooldown 60 mins)")
    merchant_e, tx_e, opp_e = seed_scenario(
        db,
        amount=Decimal("3000.00"),
        risk_level="LOW",
        prior_attempts=1,
        recovery_prob=Decimal("0.85"),
    )
    last_attempt = tx_e.payment_attempts[-1]
    last_attempt.attempted_at = utc_now() - timedelta(minutes=10)
    db.commit()

    create_policy(
        db,
        PolicyCreate(
            merchant_id=merchant_e.id,
            policy_name="Cooldown Policy",
            configuration=PolicyConfig(max_attempts=3, cooldown_minutes=60),
        ),
    )
    res_e = orchestrator.execute_recovery(
        WorkflowExecuteRequest(merchant_id=merchant_e.id, transaction_id=tx_e.id)
    )
    assert res_e.policy.decision in ["DENY", PolicyDecision.DENY]
    assert res_e.policy.checks["cooldown"] is False
    assert res_e.execution.status == "blocked"
    assert res_e.amount_recovered == 0.0
    print(f"  -> Policy Verdict: {res_e.policy.decision}")
    print(f"  -> Reason: {res_e.policy.reason}")
    print("  -> Execution: BLOCKED / WAIT")

    print("\n" + "=" * 60)
    print("ALL 6 CONTROLLED RECOVERY SCENARIOS PASSED WITH 100% INTEGRITY")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
