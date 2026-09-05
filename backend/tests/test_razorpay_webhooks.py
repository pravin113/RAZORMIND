import hashlib
import hmac
import json

from sqlalchemy import select

from app.core.config import settings
from app.db.models import AuditLog, FraudEvent, PaymentAttempt, RecoveryOpportunity, Transaction, WebhookEvent


SECRET = "test_webhook_secret"


def sign(payload: bytes) -> str:
    return hmac.new(SECRET.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def payment_payload(event: str, payment_id: str = "pay_test_123", status: str = "authorized", notes=None) -> dict:
    return {
        "event": event,
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "order_id": "order_test_123",
                    "amount": 29900,
                    "currency": "INR",
                    "status": status,
                    "method": "upi",
                    "captured": status == "captured",
                    "created_at": 1790000000,
                    "notes": notes or {},
                    "error_code": "BAD_REQUEST_ERROR" if status == "failed" else None,
                    "error_description": "Payment failed" if status == "failed" else None,
                    "error_reason": "payment_failed" if status == "failed" else None,
                }
            }
        },
    }


def post_webhook(client, payload: dict | bytes, event_id: str = "evt_test_123", signature: str | None = None):
    body = payload if isinstance(payload, bytes) else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {"x-razorpay-event-id": event_id}
    if signature is not None:
        headers["X-Razorpay-Signature"] = signature
    else:
        headers["X-Razorpay-Signature"] = sign(body)
    return client.post("/api/v1/webhooks/razorpay", content=body, headers=headers)


def test_valid_webhook_signature_processes_event(client, db_session):
    settings.razorpay_webhook_secret = SECRET

    response = post_webhook(client, payment_payload("payment.authorized"))

    assert response.status_code == 200
    assert response.json()["processed"] is True
    assert db_session.scalar(select(WebhookEvent).where(WebhookEvent.event_id == "evt_test_123")) is not None


def test_invalid_webhook_signature(client):
    settings.razorpay_webhook_secret = SECRET

    response = post_webhook(client, payment_payload("payment.authorized"), signature="bad")

    assert response.status_code == 401


def test_missing_webhook_signature(client):
    settings.razorpay_webhook_secret = SECRET
    body = json.dumps(payment_payload("payment.authorized")).encode("utf-8")

    response = client.post("/api/v1/webhooks/razorpay", content=body, headers={"x-razorpay-event-id": "evt_no_sig"})

    assert response.status_code == 401


def test_missing_webhook_secret(client):
    settings.razorpay_webhook_secret = None
    body = json.dumps(payment_payload("payment.authorized")).encode("utf-8")

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=body,
        headers={"x-razorpay-event-id": "evt_no_secret", "X-Razorpay-Signature": "anything"},
    )

    assert response.status_code == 503


def test_payment_authorized_creates_transaction(client, db_session):
    settings.razorpay_webhook_secret = SECRET

    response = post_webhook(client, payment_payload("payment.authorized"), event_id="evt_authorized")

    transaction = db_session.scalar(select(Transaction).where(Transaction.razorpay_payment_id == "pay_test_123"))
    assert response.status_code == 200
    assert transaction is not None
    assert transaction.status == "authorized"


def test_payment_captured_creates_transaction(client, db_session):
    settings.razorpay_webhook_secret = SECRET

    response = post_webhook(
        client,
        payment_payload("payment.captured", payment_id="pay_capture", status="captured"),
        event_id="evt_captured",
    )

    transaction = db_session.scalar(select(Transaction).where(Transaction.razorpay_payment_id == "pay_capture"))
    assert response.status_code == 200
    assert transaction.status == "captured"


def test_payment_failed_creates_attempt(client, db_session):
    settings.razorpay_webhook_secret = SECRET

    response = post_webhook(
        client,
        payment_payload("payment.failed", payment_id="pay_failed", status="failed"),
        event_id="evt_failed",
    )

    transaction = db_session.scalar(select(Transaction).where(Transaction.razorpay_payment_id == "pay_failed"))
    attempt = db_session.scalar(select(PaymentAttempt).where(PaymentAttempt.transaction_id == transaction.id))
    assert response.status_code == 200
    assert attempt.status == "failed"


def test_order_paid_is_supported(client, db_session):
    settings.razorpay_webhook_secret = SECRET
    payload = {"event": "order.paid", "payload": {"order": {"entity": {"id": "order_paid_123", "status": "paid"}}}}

    response = post_webhook(client, payload, event_id="evt_order_paid")

    assert response.status_code == 200
    assert db_session.scalar(select(WebhookEvent).where(WebhookEvent.event_id == "evt_order_paid")).processed is True


def test_duplicate_webhook_event_is_idempotent(client, db_session):
    settings.razorpay_webhook_secret = SECRET
    payload = payment_payload("payment.authorized", payment_id="pay_duplicate_event")

    first = post_webhook(client, payload, event_id="evt_duplicate")
    second = post_webhook(client, payload, event_id="evt_duplicate")
    transactions = db_session.scalars(
        select(Transaction).where(Transaction.razorpay_payment_id == "pay_duplicate_event")
    ).all()

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
    assert len(transactions) == 1


def test_duplicate_payment_id_does_not_create_duplicate_transaction(client, db_session):
    settings.razorpay_webhook_secret = SECRET

    post_webhook(client, payment_payload("payment.authorized", payment_id="pay_same"), event_id="evt_same_1")
    post_webhook(client, payment_payload("payment.captured", payment_id="pay_same", status="captured"), event_id="evt_same_2")
    transactions = db_session.scalars(select(Transaction).where(Transaction.razorpay_payment_id == "pay_same")).all()

    assert len(transactions) == 1
    assert transactions[0].status == "captured"


def test_out_of_order_captured_before_authorized_does_not_downgrade(client, db_session):
    settings.razorpay_webhook_secret = SECRET

    post_webhook(client, payment_payload("payment.captured", payment_id="pay_out_order", status="captured"), event_id="evt_oo_1")
    post_webhook(client, payment_payload("payment.authorized", payment_id="pay_out_order", status="authorized"), event_id="evt_oo_2")
    transaction = db_session.scalar(select(Transaction).where(Transaction.razorpay_payment_id == "pay_out_order"))

    assert transaction.status == "captured"


def test_failed_payment_creates_recovery_opportunity(client, db_session):
    settings.razorpay_webhook_secret = SECRET

    response = post_webhook(
        client,
        payment_payload("payment.failed", payment_id="pay_recovery", status="failed"),
        event_id="evt_recovery",
    )

    transaction = db_session.scalar(select(Transaction).where(Transaction.razorpay_payment_id == "pay_recovery"))
    opportunity = db_session.scalar(select(RecoveryOpportunity).where(RecoveryOpportunity.transaction_id == transaction.id))
    assert response.status_code == 200
    assert opportunity is not None


def test_high_risk_payment_creates_fraud_event(client, db_session, monkeypatch):
    settings.razorpay_webhook_secret = SECRET

    def fake_risk(db, payload):
        from app.db.models import FraudEvent, RiskScore
        from decimal import Decimal

        risk_score = RiskScore(
            transaction_id=payload.transaction_id,
            fraud_probability=Decimal("0.9900"),
            anomaly_score=Decimal("0.9000"),
            risk_score=Decimal("0.9500"),
            risk_level="CRITICAL",
            model_version="test",
        )
        db.add(risk_score)
        db.add(
            FraudEvent(
                transaction_id=payload.transaction_id,
                risk_score=risk_score,
                event_type="ml_risk_flag",
                severity="CRITICAL",
                amount_at_risk=payload.amount,
                reason="test",
                status="open",
            )
        )
        db.flush()
        return {"risk_level": "CRITICAL"}

    monkeypatch.setattr("app.services.webhook_service.run_risk_analysis", fake_risk)
    response = post_webhook(
        client,
        payment_payload("payment.captured", payment_id="pay_high_risk", status="captured"),
        event_id="evt_high_risk",
    )

    transaction = db_session.scalar(select(Transaction).where(Transaction.razorpay_payment_id == "pay_high_risk"))
    fraud_event = db_session.scalar(select(FraudEvent).where(FraudEvent.transaction_id == transaction.id))
    assert response.status_code == 200
    assert fraud_event is not None


def test_unsupported_webhook_event_is_ignored(client, db_session):
    settings.razorpay_webhook_secret = SECRET
    payload = {"event": "refund.created", "payload": {"refund": {"entity": {"id": "rfnd_test"}}}}

    response = post_webhook(client, payload, event_id="evt_unsupported")

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_malformed_payload_returns_400_after_signature_verification(client, db_session):
    settings.razorpay_webhook_secret = SECRET
    body = b"{not-json"

    response = post_webhook(client, body, event_id="evt_malformed")

    assert response.status_code == 400
    assert db_session.scalar(select(WebhookEvent).where(WebhookEvent.event_id == "evt_malformed")) is not None


def test_webhook_audit_logging(client, db_session):
    settings.razorpay_webhook_secret = SECRET

    response = post_webhook(
        client,
        payment_payload("payment.authorized", payment_id="pay_audit"),
        event_id="evt_audit",
    )

    audit = db_session.scalar(select(AuditLog).where(AuditLog.resource_id == "evt_audit"))
    assert response.status_code == 200
    assert audit is not None
    assert audit.decision == "processed"

