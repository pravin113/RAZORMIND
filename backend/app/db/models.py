from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base, GUID


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    business_type: Mapped[str] = mapped_column(String(100), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    customers: Mapped[list["Customer"]] = relationship(back_populates="merchant")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="merchant")
    revenue_events: Mapped[list["RevenueEvent"]] = relationship(back_populates="merchant")
    policies: Mapped[list["Policy"]] = relationship(back_populates="merchant")
    agent_decisions: Mapped[list["AgentDecision"]] = relationship(back_populates="merchant")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="merchant")
    documents: Mapped[list["Document"]] = relationship(back_populates="merchant")
    recovery_outcomes: Mapped[list["RecoveryOutcome"]] = relationship(back_populates="merchant")


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (Index("ix_customers_merchant_id", "merchant_id"),)

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    merchant_id: Mapped[Any] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False)
    external_customer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    merchant: Mapped["Merchant"] = relationship(back_populates="customers")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="customer")
    recovery_opportunities: Mapped[list["RecoveryOpportunity"]] = relationship(back_populates="customer")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_merchant_id", "merchant_id"),
        Index("ix_transactions_transaction_timestamp", "transaction_timestamp"),
        Index("ix_transactions_status", "status"),
        Index("ix_transactions_razorpay_payment_id", "razorpay_payment_id", unique=True),
        Index("ix_transactions_razorpay_order_id", "razorpay_order_id"),
    )

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    merchant_id: Mapped[Any] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False)
    customer_id: Mapped[Any | None] = mapped_column(GUID(), ForeignKey("customers.id"), nullable=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(100), nullable=False)
    transaction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    merchant: Mapped["Merchant"] = relationship(back_populates="transactions")
    customer: Mapped["Customer | None"] = relationship(back_populates="transactions")
    payment_attempts: Mapped[list["PaymentAttempt"]] = relationship(back_populates="transaction")
    risk_scores: Mapped[list["RiskScore"]] = relationship(back_populates="transaction")
    fraud_events: Mapped[list["FraudEvent"]] = relationship(back_populates="transaction")
    recovery_opportunities: Mapped[list["RecoveryOpportunity"]] = relationship(back_populates="transaction")
    agent_decisions: Mapped[list["AgentDecision"]] = relationship(back_populates="transaction")


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"
    __table_args__ = (Index("ix_payment_attempts_transaction_id", "transaction_id"),)

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    transaction_id: Mapped[Any] = mapped_column(GUID(), ForeignKey("transactions.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    transaction: Mapped["Transaction"] = relationship(back_populates="payment_attempts")


class RiskScore(Base):
    __tablename__ = "risk_scores"
    __table_args__ = (
        Index("ix_risk_scores_transaction_id", "transaction_id"),
        Index("ix_risk_scores_risk_level", "risk_level"),
    )

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    transaction_id: Mapped[Any] = mapped_column(GUID(), ForeignKey("transactions.id"), nullable=False)
    fraud_probability: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    anomaly_score: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    transaction: Mapped["Transaction"] = relationship(back_populates="risk_scores")
    fraud_events: Mapped[list["FraudEvent"]] = relationship(back_populates="risk_score")


class FraudEvent(Base):
    __tablename__ = "fraud_events"
    __table_args__ = (
        Index("ix_fraud_events_transaction_id", "transaction_id"),
        Index("ix_fraud_events_risk_score_id", "risk_score_id"),
    )

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    transaction_id: Mapped[Any] = mapped_column(GUID(), ForeignKey("transactions.id"), nullable=False)
    risk_score_id: Mapped[Any | None] = mapped_column(GUID(), ForeignKey("risk_scores.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    amount_at_risk: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    transaction: Mapped["Transaction"] = relationship(back_populates="fraud_events")
    risk_score: Mapped["RiskScore | None"] = relationship(back_populates="fraud_events")


class RecoveryOpportunity(Base):
    __tablename__ = "recovery_opportunities"
    __table_args__ = (
        Index("ix_recovery_opportunities_transaction_id", "transaction_id"),
        Index("ix_recovery_opportunities_customer_id", "customer_id"),
        Index("ix_recovery_opportunities_status", "status"),
    )

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    transaction_id: Mapped[Any | None] = mapped_column(GUID(), ForeignKey("transactions.id"), nullable=True)
    customer_id: Mapped[Any | None] = mapped_column(GUID(), ForeignKey("customers.id"), nullable=True)
    opportunity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    amount_at_risk: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    recovery_probability: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    transaction: Mapped["Transaction | None"] = relationship(back_populates="recovery_opportunities")
    customer: Mapped["Customer | None"] = relationship(back_populates="recovery_opportunities")
    recovery_actions: Mapped[list["RecoveryAction"]] = relationship(back_populates="opportunity")
    agent_decisions: Mapped[list["AgentDecision"]] = relationship(back_populates="opportunity")
    recovery_outcomes: Mapped[list["RecoveryOutcome"]] = relationship(back_populates="opportunity")


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"
    __table_args__ = (Index("ix_recovery_actions_opportunity_id", "opportunity_id"),)

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    opportunity_id: Mapped[Any] = mapped_column(GUID(), ForeignKey("recovery_opportunities.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_status: Mapped[str] = mapped_column(String(50), nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    opportunity: Mapped["RecoveryOpportunity"] = relationship(back_populates="recovery_actions")


class RevenueEvent(Base):
    __tablename__ = "revenue_events"
    __table_args__ = (
        Index("ix_revenue_events_merchant_id", "merchant_id"),
        Index("ix_revenue_events_event_timestamp", "event_timestamp"),
    )

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    merchant_id: Mapped[Any] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)

    merchant: Mapped["Merchant"] = relationship(back_populates="revenue_events")


class Policy(Base):
    __tablename__ = "policies"
    __table_args__ = (Index("ix_policies_merchant_id", "merchant_id"),)

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    merchant_id: Mapped[Any] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False)
    policy_name: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(100), nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="policies")


class AgentDecision(Base):
    __tablename__ = "agent_decisions"
    __table_args__ = (
        Index("ix_agent_decisions_merchant_id", "merchant_id"),
        Index("ix_agent_decisions_transaction_id", "transaction_id"),
        Index("ix_agent_decisions_opportunity_id", "opportunity_id"),
    )

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    merchant_id: Mapped[Any] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False)
    transaction_id: Mapped[Any | None] = mapped_column(GUID(), ForeignKey("transactions.id"), nullable=True)
    opportunity_id: Mapped[Any | None] = mapped_column(GUID(), ForeignKey("recovery_opportunities.id"), nullable=True)
    decision_type: Mapped[str] = mapped_column(String(100), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    policy_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    merchant: Mapped["Merchant"] = relationship(back_populates="agent_decisions")
    transaction: Mapped["Transaction | None"] = relationship(back_populates="agent_decisions")
    opportunity: Mapped["RecoveryOpportunity | None"] = relationship(back_populates="agent_decisions")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_merchant_id", "merchant_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    merchant_id: Mapped[Any | None] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=True)
    actor_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decision: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    merchant: Mapped["Merchant | None"] = relationship(back_populates="audit_logs")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_merchant_id", "merchant_id"),)

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    merchant_id: Mapped[Any | None] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    merchant: Mapped["Merchant | None"] = relationship(back_populates="documents")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (
        Index("ix_webhook_events_event_id", "event_id", unique=True),
        Index("ix_webhook_events_event_type", "event_type"),
        Index("ix_webhook_events_received_at", "received_at"),
    )

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    signature_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class RecoveryOutcome(Base):
    __tablename__ = "recovery_outcomes"
    __table_args__ = (
        Index("ix_recovery_outcomes_opportunity_id", "opportunity_id"),
        Index("ix_recovery_outcomes_merchant_id", "merchant_id"),
        Index("ix_recovery_outcomes_created_at", "created_at"),
    )

    id: Mapped[Any] = mapped_column(GUID(), primary_key=True, default=uuid4)
    opportunity_id: Mapped[Any] = mapped_column(GUID(), ForeignKey("recovery_opportunities.id"), nullable=False)
    merchant_id: Mapped[Any] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False)
    predicted_probability: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    chosen_action: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_decision: Mapped[str] = mapped_column(String(50), nullable=False)
    actual_result: Mapped[str] = mapped_column(String(50), nullable=False)
    recovered_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    prediction_correctness: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    merchant: Mapped["Merchant"] = relationship(back_populates="recovery_outcomes")
    opportunity: Mapped["RecoveryOpportunity"] = relationship(back_populates="recovery_outcomes")
