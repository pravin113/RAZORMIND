from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.ai.policy.engine import PolicyEngine
from app.ai.policy.schemas import (
    PolicyConfig,
    PolicyCreate,
    PolicyDecision,
    PolicyEvaluationRequest,
    PolicyUpdate,
)
from app.ai.policy.service import (
    create_policy,
    evaluate_merchant_policy,
    get_merchant_policy,
    get_policy,
    list_policies,
    update_policy,
)
from app.db.models import Merchant


def test_policy_engine_allow_default():
    req = PolicyEvaluationRequest(
        merchant_id=uuid4(),
        action_type="retry_payment",
        amount=2999.0,
        recovery_probability=0.82,
        attempt_number=1,
        risk_level="LOW",
        confidence=0.85,
    )
    res = PolicyEngine.evaluate(req)
    assert res.decision == PolicyDecision.ALLOW
    assert res.checks.enabled is True
    assert res.checks.amount_limit is True
    assert res.checks.probability_threshold is True
    assert res.checks.attempt_limit is True
    assert res.checks.cooldown is True
    assert res.checks.action_allowed is True
    assert res.checks.risk_acceptable is True


def test_policy_engine_deny_unsupported_action():
    req = PolicyEvaluationRequest(
        merchant_id=uuid4(),
        action_type="arbitrary_database_delete",
        amount=500.0,
        recovery_probability=0.90,
    )
    res = PolicyEngine.evaluate(req)
    assert res.decision == PolicyDecision.DENY
    assert res.checks.action_allowed is False
    assert "not permitted" in res.reason


def test_policy_engine_deny_disabled_policy():
    cfg = PolicyConfig(enabled=False)
    req = PolicyEvaluationRequest(
        merchant_id=uuid4(),
        action_type="retry_payment",
        amount=100.0,
        recovery_probability=0.90,
    )
    res = PolicyEngine.evaluate(req, config=cfg)
    assert res.decision == PolicyDecision.DENY
    assert res.checks.enabled is False
    assert "disabled" in res.reason


def test_policy_engine_stopping_rule_max_attempts():
    cfg = PolicyConfig(max_attempts=2)
    req = PolicyEvaluationRequest(
        merchant_id=uuid4(),
        action_type="retry_payment",
        amount=1000.0,
        recovery_probability=0.80,
        attempt_number=2,  # Already reached max_attempts
    )
    res = PolicyEngine.evaluate(req, config=cfg)
    assert res.decision == PolicyDecision.DENY
    assert res.checks.attempt_limit is False
    assert "Maximum recovery attempts" in res.reason


def test_policy_engine_deny_cooldown_active():
    cfg = PolicyConfig(cooldown_minutes=60)
    recent_attempt = datetime.now(timezone.utc) - timedelta(minutes=15)
    req = PolicyEvaluationRequest(
        merchant_id=uuid4(),
        action_type="retry_payment",
        amount=500.0,
        recovery_probability=0.85,
        attempt_number=1,
        last_attempt_at=recent_attempt,
    )
    res = PolicyEngine.evaluate(req, config=cfg)
    assert res.decision == PolicyDecision.DENY
    assert res.checks.cooldown is False
    assert "Cooldown active" in res.reason


def test_policy_engine_require_review_high_risk():
    req = PolicyEvaluationRequest(
        merchant_id=uuid4(),
        action_type="retry_payment",
        amount=500.0,
        recovery_probability=0.85,
        attempt_number=1,
        risk_level="HIGH",
    )
    res = PolicyEngine.evaluate(req)
    assert res.decision == PolicyDecision.REQUIRE_REVIEW
    assert res.checks.risk_acceptable is False
    assert "risk level 'HIGH' requires human review" in res.reason


def test_policy_engine_require_review_low_probability():
    cfg = PolicyConfig(min_recovery_probability=0.65)
    req = PolicyEvaluationRequest(
        merchant_id=uuid4(),
        action_type="retry_payment",
        amount=500.0,
        recovery_probability=0.45,
        attempt_number=1,
        risk_level="LOW",
    )
    res = PolicyEngine.evaluate(req, config=cfg)
    assert res.decision == PolicyDecision.REQUIRE_REVIEW
    assert res.checks.probability_threshold is False
    assert "below minimum threshold" in res.reason


def test_policy_engine_require_review_amount_exceeded():
    cfg = PolicyConfig(max_recovery_amount=10000.0)
    req = PolicyEvaluationRequest(
        merchant_id=uuid4(),
        action_type="retry_payment",
        amount=25000.0,
        recovery_probability=0.85,
        attempt_number=1,
        risk_level="LOW",
    )
    res = PolicyEngine.evaluate(req, config=cfg)
    assert res.decision == PolicyDecision.REQUIRE_REVIEW
    assert res.checks.amount_limit is False
    assert "exceeds automated threshold" in res.reason


def test_policy_service_crud_and_evaluate(db_session):
    merchant = Merchant(
        name="Policy Test Merchant",
        email=f"merchant_{uuid4().hex[:8]}@example.com",
        business_type="ecommerce",
        currency="INR",
    )
    db_session.add(merchant)
    db_session.commit()

    # Create policy
    create_payload = PolicyCreate(
        merchant_id=merchant.id,
        policy_name="Custom Recovery Policy",
        policy_type="recovery",
        configuration=PolicyConfig(
            min_recovery_probability=0.75,
            max_recovery_amount=5000.0,
            max_attempts=3,
        ),
        enabled=True,
    )
    created = create_policy(db_session, create_payload)
    assert created.id is not None
    assert created.policy_name == "Custom Recovery Policy"

    # Get policy
    fetched = get_policy(db_session, created.id)
    assert fetched is not None
    assert fetched.merchant_id == merchant.id

    # Get merchant policy
    m_policy = get_merchant_policy(db_session, merchant.id, policy_type="recovery")
    assert m_policy is not None
    assert m_policy.id == created.id

    # List policies
    policies = list_policies(db_session, merchant_id=merchant.id)
    assert len(policies) == 1

    # Update policy
    updated = update_policy(
        db_session,
        created.id,
        PolicyUpdate(policy_name="Renamed Policy", enabled=False),
    )
    assert updated.policy_name == "Renamed Policy"
    assert updated.enabled is False


def test_policy_api_endpoints(client: TestClient, db_session):
    merchant = Merchant(
        name="API Policy Merchant",
        email=f"api_{uuid4().hex[:8]}@example.com",
        business_type="retail",
        currency="INR",
    )
    db_session.add(merchant)
    db_session.commit()

    # 1. Create policy via API
    res = client.post(
        "/api/v1/policies",
        json={
            "merchant_id": str(merchant.id),
            "policy_name": "Standard Store Policy",
            "policy_type": "recovery",
            "configuration": {
                "enabled": True,
                "min_recovery_probability": 0.60,
                "max_recovery_amount": 15000.0,
                "max_attempts": 2,
                "cooldown_minutes": 30,
                "allowed_actions": ["retry_payment", "send_payment_reminder"],
            },
            "enabled": True,
        },
    )
    assert res.status_code == 201
    policy_id = res.json()["id"]

    # 2. Get policy via API
    res = client.get(f"/api/v1/policies/{policy_id}")
    assert res.status_code == 200
    assert res.json()["policy_name"] == "Standard Store Policy"

    # 3. List policies via API
    res = client.get(f"/api/v1/policies?merchant_id={merchant.id}")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 4. Evaluate policy via API
    res = client.post(
        "/api/v1/policies/evaluate",
        json={
            "merchant_id": str(merchant.id),
            "action_type": "retry_payment",
            "amount": 2990.0,
            "recovery_probability": 0.81,
            "attempt_number": 1,
            "risk_level": "LOW",
        },
    )
    assert res.status_code == 200
    eval_data = res.json()
    assert eval_data["decision"] == "ALLOW"
    assert eval_data["checks"]["amount_limit"] is True
    assert eval_data["checks"]["probability_threshold"] is True
