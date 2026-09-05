from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.ai.policy.schemas import PolicyConfig, PolicyCreate
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


def _seed_merchant_and_transaction(
    db_session,
    amount: Decimal = Decimal("2999.00"),
    status: str = "failed",
    risk_level: str = "LOW",
    prior_attempts: int = 0,
    recovery_prob: Decimal = Decimal("0.82"),
) -> tuple[Merchant, Transaction, RecoveryOpportunity]:
    merchant = Merchant(
        name="Workflow Test Merchant",
        email=f"workflow_{uuid4().hex[:8]}@example.com",
        business_type="ecommerce",
        currency="INR",
    )
    db_session.add(merchant)
    db_session.flush()

    customer = Customer(
        merchant_id=merchant.id,
        external_customer_id=f"cust_{uuid4().hex[:6]}",
        name="Test Customer",
        email="customer@example.com",
    )
    db_session.add(customer)
    db_session.flush()

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
    db_session.add(tx)
    db_session.flush()

    # Risk score
    risk = RiskScore(
        transaction_id=tx.id,
        fraud_probability=Decimal("0.05") if risk_level == "LOW" else Decimal("0.85"),
        anomaly_score=Decimal("0.10"),
        risk_score=Decimal("0.10") if risk_level == "LOW" else Decimal("0.88"),
        risk_level=risk_level,
        model_version="v1.0.0",
        created_at=utc_now(),
    )
    db_session.add(risk)

    # Prior attempts
    for i in range(prior_attempts):
        db_session.add(
            PaymentAttempt(
                transaction_id=tx.id,
                attempt_number=i + 1,
                status="failed",
                failure_code="insufficient_funds",
                attempted_at=utc_now() - timedelta(hours=2 * (prior_attempts - i)),
            )
        )

    # Recovery opportunity
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
    db_session.add(opp)
    db_session.commit()
    return merchant, tx, opp


def test_successful_autonomous_recovery_workflow(db_session):
    # Base scenario: ₹2,999, failed, recovery prob 0.82, LOW risk, attempt 0
    merchant, tx, opp = _seed_merchant_and_transaction(
        db_session,
        amount=Decimal("2999.00"),
        status="failed",
        risk_level="LOW",
        prior_attempts=0,
        recovery_prob=Decimal("0.82"),
    )

    # Configure policy: min prob 0.65, max amount ₹10,000, max attempts 2
    create_policy(
        db_session,
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

    orchestrator = RevenueRecoveryOrchestrator(db_session)
    res = orchestrator.execute_recovery(
        WorkflowExecuteRequest(
            merchant_id=merchant.id,
            transaction_id=tx.id,
            opportunity_id=opp.id,
        )
    )

    assert res.status == "completed"
    assert res.decision.action == "retry_payment"
    assert res.policy.decision == "ALLOW"
    assert res.execution.status == "success"
    assert res.verification.status == "recovered"
    assert res.amount_recovered == 2999.0
    assert "get_transaction" in res.tools_used or "get_recovery_summary" in res.tools_used

    # Verify database persistence
    # 1. AgentDecision
    decision_rec = db_session.scalars(
        select(AgentDecision).where(AgentDecision.merchant_id == merchant.id)
    ).first()
    assert decision_rec is not None
    assert decision_rec.recommended_action == "retry_payment"

    # 2. AuditLog
    audit_rec = db_session.scalars(
        select(AuditLog).where(AuditLog.merchant_id == merchant.id)
    ).first()
    assert audit_rec is not None
    assert audit_rec.decision == "ALLOW"

    # 3. RecoveryOutcome
    outcome_rec = db_session.scalars(
        select(RecoveryOutcome).where(RecoveryOutcome.merchant_id == merchant.id)
    ).first()
    assert outcome_rec is not None
    assert outcome_rec.actual_result == "recovered"
    assert outcome_rec.recovered_amount == Decimal("2999.00")
    assert outcome_rec.prediction_correctness is True


def test_negative_scenario_high_risk_requires_review(db_session):
    # Negative Scenario 1: High risk payment -> REQUIRE_REVIEW
    merchant, tx, opp = _seed_merchant_and_transaction(
        db_session,
        amount=Decimal("2999.00"),
        risk_level="HIGH",
        recovery_prob=Decimal("0.85"),
    )

    orchestrator = RevenueRecoveryOrchestrator(db_session)
    res = orchestrator.execute_recovery(
        WorkflowExecuteRequest(
            merchant_id=merchant.id,
            transaction_id=tx.id,
        )
    )

    # Action is blocked, requires human review
    assert res.decision.action == "escalate_to_human"
    assert res.policy.decision in ["REQUIRE_REVIEW", "DENY"]
    assert res.execution.status == "blocked"
    assert res.verification.status in ["queued_for_review", "stopped"]
    assert res.amount_recovered == 0.0


def test_negative_scenario_low_probability_requires_review(db_session):
    # Negative Scenario 2: Low recovery probability (0.45 < 0.65) -> REQUIRE_REVIEW
    merchant, tx, opp = _seed_merchant_and_transaction(
        db_session,
        amount=Decimal("1500.00"),
        risk_level="LOW",
        recovery_prob=Decimal("0.45"),
    )

    create_policy(
        db_session,
        PolicyCreate(
            merchant_id=merchant.id,
            policy_name="Strict Prob Policy",
            configuration=PolicyConfig(min_recovery_probability=0.65),
        ),
    )

    orchestrator = RevenueRecoveryOrchestrator(db_session)
    res = orchestrator.execute_recovery(
        WorkflowExecuteRequest(
            merchant_id=merchant.id,
            transaction_id=tx.id,
        )
    )

    assert res.policy.decision == "REQUIRE_REVIEW"
    assert res.execution.status == "blocked"
    assert res.amount_recovered == 0.0


def test_negative_scenario_amount_exceeds_limit(db_session):
    # Negative Scenario 3: Amount ₹25,000 exceeds ₹10,000 limit -> REQUIRE_REVIEW
    merchant, tx, opp = _seed_merchant_and_transaction(
        db_session,
        amount=Decimal("25000.00"),
        risk_level="LOW",
        recovery_prob=Decimal("0.80"),
    )

    create_policy(
        db_session,
        PolicyCreate(
            merchant_id=merchant.id,
            policy_name="Amount Limit Policy",
            configuration=PolicyConfig(max_recovery_amount=10000.0),
        ),
    )

    orchestrator = RevenueRecoveryOrchestrator(db_session)
    res = orchestrator.execute_recovery(
        WorkflowExecuteRequest(
            merchant_id=merchant.id,
            transaction_id=tx.id,
        )
    )

    assert res.policy.decision == "REQUIRE_REVIEW"
    assert res.execution.status == "blocked"
    assert res.amount_recovered == 0.0


def test_negative_scenario_max_attempts_stopping_rule(db_session):
    # Negative Scenario 4: Prior attempts = 2, max attempts = 2 -> STOP / DENY
    merchant, tx, opp = _seed_merchant_and_transaction(
        db_session,
        amount=Decimal("3000.00"),
        risk_level="LOW",
        prior_attempts=2,
        recovery_prob=Decimal("0.85"),
    )

    create_policy(
        db_session,
        PolicyCreate(
            merchant_id=merchant.id,
            policy_name="Max 2 Attempts Policy",
            configuration=PolicyConfig(max_attempts=2),
        ),
    )

    orchestrator = RevenueRecoveryOrchestrator(db_session)
    res = orchestrator.execute_recovery(
        WorkflowExecuteRequest(
            merchant_id=merchant.id,
            transaction_id=tx.id,
        )
    )

    assert res.policy.decision == "DENY"
    assert res.execution.status == "blocked"
    assert res.verification.status == "stopped"
    assert res.amount_recovered == 0.0


def test_negative_scenario_cooldown_active(db_session):
    # Negative Scenario 5: Last attempt was 10 mins ago, cooldown is 60 mins -> DENY / WAIT
    merchant, tx, opp = _seed_merchant_and_transaction(
        db_session,
        amount=Decimal("3000.00"),
        risk_level="LOW",
        prior_attempts=1,
        recovery_prob=Decimal("0.85"),
    )

    # Set last attempt to 10 minutes ago
    last_attempt = tx.payment_attempts[-1]
    last_attempt.attempted_at = utc_now() - timedelta(minutes=10)
    db_session.commit()

    create_policy(
        db_session,
        PolicyCreate(
            merchant_id=merchant.id,
            policy_name="Cooldown Policy",
            configuration=PolicyConfig(max_attempts=3, cooldown_minutes=60),
        ),
    )

    orchestrator = RevenueRecoveryOrchestrator(db_session)
    res = orchestrator.execute_recovery(
        WorkflowExecuteRequest(
            merchant_id=merchant.id,
            transaction_id=tx.id,
        )
    )

    assert res.policy.decision == "DENY"
    assert res.policy.checks["cooldown"] is False
    assert "Cooldown active" in res.policy.reason


def test_recovery_api_endpoints(client: TestClient, db_session):
    merchant, tx, opp = _seed_merchant_and_transaction(
        db_session,
        amount=Decimal("1999.00"),
        risk_level="LOW",
        prior_attempts=0,
        recovery_prob=Decimal("0.85"),
    )

    # 1. Execute recovery via API
    res = client.post(
        "/api/v1/recovery/execute",
        json={
            "merchant_id": str(merchant.id),
            "transaction_id": str(tx.id),
            "opportunity_id": str(opp.id),
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["policy"]["decision"] == "ALLOW"
    assert data["amount_recovered"] == 1999.0
    outcome_id = data["outcome_id"]
    assert outcome_id is not None

    # 2. List outcomes via API
    res = client.get(f"/api/v1/recovery/outcomes?merchant_id={merchant.id}")
    assert res.status_code == 200
    outcomes = res.json()
    assert len(outcomes) >= 1
    assert outcomes[0]["actual_result"] == "recovered"

    # 3. Get single workflow outcome via API
    res = client.get(f"/api/v1/recovery/workflows/{outcome_id}")
    assert res.status_code == 200
    assert res.json()["id"] == outcome_id
