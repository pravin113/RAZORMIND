"""
RazorMind AI — Deterministic Demo Seeding Script
Creates or resets standard buildathon demo data for live presentation:
1. Demo Merchant (UUID: 24858aff-1023-4415-9df6-58d8c5495fdd)
2. Deterministic Recovery Policy (65% min prob, ₹10,000 max amount, 2 attempts)
3. Primary Demo Failed Transaction: ₹2,999 (LOW Risk, 82% Recovery Yield, open opportunity)
4. Negative Case Transaction: ₹24,500 (HIGH Risk, Anomaly, Policy Stopping Rule demo)
"""
from __future__ import annotations

import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

sys.path.append(str(Path(__file__).resolve().parents[1]))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.ai.policy.schemas import PolicyConfig, PolicyCreate
from app.ai.policy.service import create_policy, get_merchant_policy
from app.db.models import (
    Customer,
    Merchant,
    PaymentAttempt,
    RecoveryOpportunity,
    RiskScore,
    Transaction,
    utc_now,
)
from app.db.session import SessionLocal

DEMO_MERCHANT_ID = UUID("24858aff-1023-4415-9df6-58d8c5495fdd")
PRIMARY_TX_ID = UUID("3e074091-098a-4a56-9583-5c686fb066da")
PRIMARY_OPP_ID = UUID("1f5b098c-5ae4-403e-a68a-ae70a957d089")
NEGATIVE_TX_ID = UUID("4f185092-109b-4b67-8694-6d797fc177eb")
NEGATIVE_OPP_ID = UUID("2a6c109d-6bf5-414f-b79b-bf81ba68e190")


def seed_demo_data() -> None:
    db = SessionLocal()
    print("=" * 60)
    print("RAZORMIND AI — SEEDING REPRODUCIBLE BUILDATHON DEMO DATA")
    print("=" * 60)

    try:
        # 1. Demo Merchant
        merchant = db.get(Merchant, DEMO_MERCHANT_ID)
        if not merchant:
            merchant = Merchant(
                id=DEMO_MERCHANT_ID,
                name="Apex Global Enterprise",
                email="demo@razormind.ai",
                business_type="ecommerce",
                currency="INR",
            )
            db.add(merchant)
            db.flush()
            print(f"[+] Created Demo Merchant: {merchant.name} ({merchant.id})")
        else:
            print(f"[i] Existing Demo Merchant verified: {merchant.name}")

        # 2. Demo Customer
        customer = db.query(Customer).filter(Customer.merchant_id == merchant.id).first()
        if not customer:
            customer = Customer(
                merchant_id=merchant.id,
                external_customer_id="cust_apex_9981",
                name="Rohan Sharma",
                email="rohan.sharma@example.com",
            )
            db.add(customer)
            db.flush()
            print(f"[+] Created Demo Customer: {customer.name}")

        # 3. Deterministic Policy
        policy = get_merchant_policy(db, merchant.id, policy_type="recovery")
        if not policy:
            policy = create_policy(
                db,
                PolicyCreate(
                    merchant_id=merchant.id,
                    policy_name="Standard Autonomous Recovery Policy",
                    policy_type="recovery",
                    configuration=PolicyConfig(
                        enabled=True,
                        min_recovery_probability=0.65,
                        max_recovery_amount=10000.0,
                        max_attempts=2,
                        cooldown_minutes=60,
                        allowed_actions=["retry_payment", "send_payment_reminder", "create_followup"],
                        risk_restrictions=["HIGH", "CRITICAL"],
                    ),
                ),
            )
            print("[+] Configured Deterministic Policy Engine guardrails (min prob 65%, max INR 10,000)")
        else:
            print("[i] Active Recovery Policy Engine guardrails verified")

        # 4. Primary Demo Failed Payment (₹2,999 - Eligible for autonomous recovery)
        primary_tx = db.get(Transaction, PRIMARY_TX_ID)
        if primary_tx:
            primary_tx.status = "failed"
            primary_tx.amount = Decimal("2999.00")
            primary_tx.payment_method = "card"
            primary_tx.transaction_timestamp = utc_now()
        else:
            primary_tx = Transaction(
                id=PRIMARY_TX_ID,
                merchant_id=merchant.id,
                customer_id=customer.id,
                amount=Decimal("2999.00"),
                currency="INR",
                status="failed",
                payment_method="card",
                transaction_timestamp=utc_now(),
                metadata_={"failure_reason": "temporary_bank_downtime", "test_mode": True},
            )
            db.add(primary_tx)
            db.flush()

        # Risk score for primary transaction (LOW)
        primary_risk = db.query(RiskScore).filter(RiskScore.transaction_id == primary_tx.id).first()
        if not primary_risk:
            primary_risk = RiskScore(
                transaction_id=primary_tx.id,
                fraud_probability=Decimal("0.04"),
                anomaly_score=Decimal("0.08"),
                risk_score=Decimal("0.08"),
                risk_level="LOW",
                model_version="CatBoost-v1.4.2",
                created_at=utc_now(),
            )
            db.add(primary_risk)

        # Recovery opportunity for primary transaction
        primary_opp = db.get(RecoveryOpportunity, PRIMARY_OPP_ID)
        if primary_opp:
            primary_opp.status = "open"
            primary_opp.amount_at_risk = Decimal("2999.00")
            primary_opp.recovery_probability = Decimal("0.82")
            primary_opp.priority = "HIGH"
            primary_opp.recommended_action = "retry_payment"
        else:
            primary_opp = RecoveryOpportunity(
                id=PRIMARY_OPP_ID,
                transaction_id=primary_tx.id,
                customer_id=customer.id,
                opportunity_type="automated_retry",
                amount_at_risk=Decimal("2999.00"),
                recovery_probability=Decimal("0.82"),
                priority="HIGH",
                status="open",
                recommended_action="retry_payment",
                created_at=utc_now(),
            )
            db.add(primary_opp)

        print("[+] Primary Demo Scenario Initialized:")
        print(f"    Transaction: ₹{primary_tx.amount:,.2f} | Status: failed | Risk: LOW (0.08)")
        print(f"    Opportunity: Prob: {float(primary_opp.recovery_probability):.0%} | Action: retry_payment | Status: open")

        # 5. Negative Scenario Payment (₹24,500 - Exceeds ₹10,000 threshold & HIGH risk)
        neg_tx = db.get(Transaction, NEGATIVE_TX_ID)
        if neg_tx:
            neg_tx.status = "failed"
            neg_tx.amount = Decimal("24500.00")
            neg_tx.payment_method = "netbanking"
            neg_tx.transaction_timestamp = utc_now() - timedelta(minutes=15)
        else:
            neg_tx = Transaction(
                id=NEGATIVE_TX_ID,
                merchant_id=merchant.id,
                customer_id=customer.id,
                amount=Decimal("24500.00"),
                currency="INR",
                status="failed",
                payment_method="netbanking",
                transaction_timestamp=utc_now() - timedelta(minutes=15),
                metadata_={"failure_reason": "velocity_limit_exceeded", "test_mode": True},
            )
            db.add(neg_tx)
            db.flush()

        neg_risk = db.query(RiskScore).filter(RiskScore.transaction_id == neg_tx.id).first()
        if not neg_risk:
            neg_risk = RiskScore(
                transaction_id=neg_tx.id,
                fraud_probability=Decimal("0.88"),
                anomaly_score=Decimal("0.91"),
                risk_score=Decimal("0.89"),
                risk_level="HIGH",
                model_version="CatBoost-v1.4.2",
                created_at=utc_now(),
            )
            db.add(neg_risk)

        neg_opp = db.get(RecoveryOpportunity, NEGATIVE_OPP_ID)
        if neg_opp:
            neg_opp.status = "open"
            neg_opp.amount_at_risk = Decimal("24500.00")
            neg_opp.recovery_probability = Decimal("0.35")
            neg_opp.priority = "CRITICAL"
            neg_opp.recommended_action = "escalate_to_human"
        else:
            neg_opp = RecoveryOpportunity(
                id=NEGATIVE_OPP_ID,
                transaction_id=neg_tx.id,
                customer_id=customer.id,
                opportunity_type="manual_review",
                amount_at_risk=Decimal("24500.00"),
                recovery_probability=Decimal("0.35"),
                priority="CRITICAL",
                status="open",
                recommended_action="escalate_to_human",
                created_at=utc_now(),
            )
            db.add(neg_opp)

        print("[+] Negative Policy Guardrail Scenario Initialized:")
        print(f"    Transaction: ₹{neg_tx.amount:,.2f} | Status: failed | Risk: HIGH (0.89)")
        print(f"    Opportunity: Prob: {float(neg_opp.recovery_probability):.0%} | Action: escalate_to_human | Policy will: REQUIRE_REVIEW")

        db.commit()
        print("=" * 60)
        print("BUILDATHON DEMO ENVIRONMENT READY")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding demo data: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
