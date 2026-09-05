from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_hmac_sha256
from app.db.models import AuditLog, Merchant, PaymentAttempt, RecoveryOpportunity, Transaction, WebhookEvent
from app.schemas.analysis import TransactionAnalysisInput
from app.services.ml_analysis import run_recovery_analysis, run_risk_analysis

logger = logging.getLogger(__name__)

SUPPORTED_EVENTS = {"payment.authorized", "payment.captured", "payment.failed", "order.paid"}
STATUS_PRECEDENCE = {
    "created": 0,
    "authorized": 1,
    "failed": 2,
    "captured": 3,
    "paid": 4,
}


class WebhookProcessingError(RuntimeError):
    pass


class WebhookSignatureError(RuntimeError):
    pass


class WebhookSecretNotConfigured(RuntimeError):
    pass


def verify_razorpay_signature(raw_body: bytes, signature: str | None) -> None:
    if not settings.razorpay_webhook_secret:
        raise WebhookSecretNotConfigured("Razorpay webhook secret is not configured")
    if not signature:
        raise WebhookSignatureError("Missing Razorpay webhook signature")
    if not verify_hmac_sha256(settings.razorpay_webhook_secret, raw_body, signature):
        raise WebhookSignatureError("Invalid Razorpay webhook signature")


def process_razorpay_webhook(db: Session, raw_body: bytes, signature: str | None, event_id: str | None) -> dict:
    verify_razorpay_signature(raw_body, signature)

    existing = _get_existing_event(db, event_id)
    if existing and existing.processed:
        return {
            "status": "duplicate",
            "event_id": event_id,
            "event_type": existing.event_type,
            "processed": True,
        }

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        event = existing or WebhookEvent(
            event_id=event_id,
            event_type="malformed",
            signature_verified=True,
            payload={},
            processed=False,
            error_message="Malformed JSON payload",
        )
        db.add(event)
        _audit(db, event_id, "malformed", "failed", "Malformed JSON payload")
        db.commit()
        raise WebhookProcessingError("Malformed JSON payload") from exc

    event_type = payload.get("event") or payload.get("event_type") or "unknown"
    event = existing or WebhookEvent(
        event_id=event_id,
        event_type=event_type,
        signature_verified=True,
        payload=payload,
    )
    event.event_type = event_type
    event.signature_verified = True
    event.payload = payload
    db.add(event)

    try:
        if event_type not in SUPPORTED_EVENTS:
            event.processed = True
            event.processed_at = _utc_now()
            _audit(db, event_id, event_type, "ignored", "Unsupported webhook event")
            db.commit()
            return {"status": "ignored", "event_id": event_id, "event_type": event_type, "processed": True}

        _dispatch_event(db, event_type, payload)
        event.processed = True
        event.processed_at = _utc_now()
        event.error_message = None
        _audit(db, event_id, event_type, "processed", None)
        db.commit()
        return {"status": "processed", "event_id": event_id, "event_type": event_type, "processed": True}
    except Exception as exc:
        db.rollback()
        event = _get_existing_event(db, event_id) or event
        event.error_message = "Webhook processing failed"
        event.processed = False
        db.add(event)
        _audit(db, event_id, event_type, "failed", "Webhook processing failed")
        db.commit()
        logger.exception("Razorpay webhook processing failed for event type %s", event_type)
        raise WebhookProcessingError("Webhook processing failed") from exc


def _dispatch_event(db: Session, event_type: str, payload: dict[str, Any]) -> None:
    if event_type in {"payment.authorized", "payment.captured", "payment.failed"}:
        payment = _extract_entity(payload, "payment")
        transaction = upsert_transaction_from_payment(db, payment)
        if event_type == "payment.failed":
            upsert_failed_payment_attempt(db, transaction, payment)
            _run_recovery_safely(db, transaction, payment)
        else:
            _run_risk_safely(db, transaction, payment)
        return

    if event_type == "order.paid":
        order = _extract_entity(payload, "order")
        _audit(db, payload.get("id"), "order.paid", "processed", None, resource_id=order.get("id"))


def upsert_transaction_from_payment(db: Session, payment: dict[str, Any]) -> Transaction:
    payment_id = payment.get("id")
    if not payment_id:
        raise WebhookProcessingError("Missing Razorpay payment ID")

    transaction = db.scalar(select(Transaction).where(Transaction.razorpay_payment_id == payment_id))
    status = str(payment.get("status") or "created")
    timestamp = _timestamp_from_razorpay(payment.get("created_at"))
    amount = _major_amount(payment.get("amount", 0), payment.get("currency", "INR"))

    if transaction is None:
        transaction = Transaction(
            merchant_id=_merchant_id_from_payment(db, payment),
            razorpay_payment_id=payment_id,
            razorpay_order_id=payment.get("order_id"),
            amount=amount,
            currency=str(payment.get("currency") or "INR"),
            status=status,
            payment_method=str(payment.get("method") or "unknown"),
            transaction_timestamp=timestamp,
            metadata_=_safe_payment_metadata(payment),
        )
        db.add(transaction)
        db.flush()
        return transaction

    transaction.razorpay_order_id = transaction.razorpay_order_id or payment.get("order_id")
    transaction.payment_method = str(payment.get("method") or transaction.payment_method or "unknown")
    transaction.amount = amount or transaction.amount
    transaction.currency = str(payment.get("currency") or transaction.currency)
    if _status_precedence(status) >= _status_precedence(transaction.status):
        transaction.status = status
    transaction.metadata_ = {**(transaction.metadata_ or {}), **_safe_payment_metadata(payment)}
    db.flush()
    return transaction


def upsert_failed_payment_attempt(db: Session, transaction: Transaction, payment: dict[str, Any]) -> PaymentAttempt:
    failure_code = payment.get("error_code")
    existing = db.scalar(
        select(PaymentAttempt).where(
            PaymentAttempt.transaction_id == transaction.id,
            PaymentAttempt.status == "failed",
            PaymentAttempt.failure_code == failure_code,
        )
    )
    if existing:
        existing.failure_reason = payment.get("error_description") or existing.failure_reason
        db.flush()
        return existing

    attempt_count = db.scalar(select(func.count(PaymentAttempt.id)).where(PaymentAttempt.transaction_id == transaction.id)) or 0
    attempt = PaymentAttempt(
        transaction_id=transaction.id,
        attempt_number=int(attempt_count) + 1,
        status="failed",
        failure_code=failure_code,
        failure_reason=payment.get("error_description") or payment.get("error_reason"),
        attempted_at=_timestamp_from_razorpay(payment.get("created_at")),
    )
    db.add(attempt)
    db.flush()
    return attempt


def _run_risk_safely(db: Session, transaction: Transaction, payment: dict[str, Any]) -> None:
    try:
        run_risk_analysis(db, _analysis_payload(transaction, payment))
    except Exception:
        db.rollback()
        db.add(transaction)
        _audit(db, None, "risk.analysis", "failed", "Risk analysis failed", resource_id=transaction.razorpay_payment_id)


def _run_recovery_safely(db: Session, transaction: Transaction, payment: dict[str, Any]) -> None:
    existing = db.scalar(
        select(RecoveryOpportunity).where(
            RecoveryOpportunity.transaction_id == transaction.id,
            RecoveryOpportunity.opportunity_type == "payment_recovery",
        )
    )
    if existing:
        return
    try:
        run_recovery_analysis(db, _analysis_payload(transaction, payment, payment_failure=1))
    except Exception:
        db.rollback()
        db.add(transaction)
        _audit(db, None, "recovery.analysis", "failed", "Recovery analysis failed", resource_id=transaction.razorpay_payment_id)


def _analysis_payload(transaction: Transaction, payment: dict[str, Any], payment_failure: int = 0) -> TransactionAnalysisInput:
    created_at = transaction.transaction_timestamp
    notes = payment.get("notes") if isinstance(payment.get("notes"), dict) else {}
    return TransactionAnalysisInput(
        transaction_id=transaction.id,
        merchant_id=transaction.merchant_id,
        amount=transaction.amount,
        currency=transaction.currency,
        payment_method=transaction.payment_method,
        transaction_hour=created_at.hour,
        day_of_week=created_at.weekday(),
        customer_transaction_count=int(notes.get("customer_transaction_count", 1) or 1),
        customer_avg_amount=Decimal(str(notes.get("customer_avg_amount", transaction.amount))),
        merchant_avg_amount=Decimal(str(notes.get("merchant_avg_amount", transaction.amount))),
        amount_deviation=float(notes.get("amount_deviation", 0) or 0),
        customer_age_days=int(notes.get("customer_age_days", 0) or 0),
        failed_attempts=int(notes.get("failed_attempts", 1 if payment_failure else 0) or 0),
        device_change=int(notes.get("device_change", 0) or 0),
        ip_change=int(notes.get("ip_change", 0) or 0),
        country_change=int(notes.get("country_change", 0) or 0),
        velocity_1h=int(notes.get("velocity_1h", 0) or 0),
        velocity_24h=int(notes.get("velocity_24h", 0) or 0),
        previous_chargebacks=int(notes.get("previous_chargebacks", 0) or 0),
        previous_fraud_events=int(notes.get("previous_fraud_events", 0) or 0),
        checkout_duration=float(notes.get("checkout_duration", 0) or 0),
        retry_count=int(notes.get("retry_count", 0) or 0),
        subscription=int(notes.get("subscription", 0) or 0),
        transaction_status=transaction.status,
        payment_failure=payment_failure,
        failure_reason=str(payment.get("error_reason") or payment.get("error_description") or "none"),
        subscription_status=str(notes.get("subscription_status", "none")),
        customer_value=Decimal(str(notes.get("customer_value", transaction.amount))),
        previous_successful_payments=int(notes.get("previous_successful_payments", 0) or 0),
        recovery_attempts=int(notes.get("recovery_attempts", 0) or 0),
    )


def _extract_entity(payload: dict[str, Any], name: str) -> dict[str, Any]:
    entity = payload.get("payload", {}).get(name, {}).get("entity")
    if not isinstance(entity, dict):
        raise WebhookProcessingError(f"Missing {name} entity")
    return entity


def _merchant_id_from_payment(db: Session, payment: dict[str, Any]):
    notes = payment.get("notes")
    if isinstance(notes, dict) and notes.get("merchant_id"):
        try:
            merchant_id = UUID(str(notes["merchant_id"]))
            if db.get(Merchant, merchant_id):
                return merchant_id
        except ValueError:
            pass
    merchant = db.scalar(select(Merchant).where(Merchant.email == "razorpay-webhooks@razormind.local"))
    if merchant is None:
        merchant = Merchant(
            name="Razorpay Webhook Merchant",
            email="razorpay-webhooks@razormind.local",
            business_type="platform",
            currency=str(payment.get("currency") or "INR"),
        )
        db.add(merchant)
        db.flush()
    return merchant.id


def _safe_payment_metadata(payment: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "razorpay_webhook",
        "order_id": payment.get("order_id"),
        "captured": payment.get("captured"),
        "description": payment.get("description"),
        "notes": payment.get("notes") if isinstance(payment.get("notes"), dict) else {},
        "error_code": payment.get("error_code"),
        "error_description": payment.get("error_description"),
    }


def _audit(
    db: Session,
    event_id: str | None,
    event_type: str,
    decision: str,
    reason: str | None,
    resource_id: str | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_type="system",
            actor_id="razorpay_webhook",
            action="process_webhook",
            resource_type="razorpay_webhook",
            resource_id=resource_id or event_id,
            decision=decision,
            reason=reason,
            metadata_={"event_id": event_id, "event_type": event_type},
        )
    )


def _get_existing_event(db: Session, event_id: str | None) -> WebhookEvent | None:
    if not event_id:
        return None
    return db.scalar(select(WebhookEvent).where(WebhookEvent.event_id == event_id))


def _major_amount(amount: Any, currency: str) -> Decimal:
    divisor = Decimal("100") if str(currency).upper() in {"INR", "USD"} else Decimal("1")
    return Decimal(str(amount or 0)) / divisor


def _timestamp_from_razorpay(value: Any) -> datetime:
    if value:
        return datetime.fromtimestamp(int(value), timezone.utc)
    return _utc_now()


def _status_precedence(status: str) -> int:
    return STATUS_PRECEDENCE.get(status, 0)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
