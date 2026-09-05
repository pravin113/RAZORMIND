"""Initial RazorMind AI database schema.

Revision ID: 001_initial_database_schema
Revises:
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_database_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


uuid_type = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "merchants",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("business_type", sa.String(length=100), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_merchants_email", "merchants", ["email"], unique=True)

    op.create_table(
        "customers",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("merchant_id", uuid_type, sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("external_customer_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_customers_merchant_id", "customers", ["merchant_id"])

    op.create_table(
        "transactions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("merchant_id", uuid_type, sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("customer_id", uuid_type, sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("razorpay_payment_id", sa.String(length=255), nullable=True),
        sa.Column("razorpay_order_id", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("payment_method", sa.String(length=100), nullable=False),
        sa.Column("transaction_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_transactions_merchant_id", "transactions", ["merchant_id"])
    op.create_index("ix_transactions_status", "transactions", ["status"])
    op.create_index("ix_transactions_transaction_timestamp", "transactions", ["transaction_timestamp"])

    op.create_table(
        "payment_attempts",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("transaction_id", uuid_type, sa.ForeignKey("transactions.id"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("failure_code", sa.String(length=100), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payment_attempts_transaction_id", "payment_attempts", ["transaction_id"])

    op.create_table(
        "risk_scores",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("transaction_id", uuid_type, sa.ForeignKey("transactions.id"), nullable=False),
        sa.Column("fraud_probability", sa.Numeric(5, 4), nullable=False),
        sa.Column("anomaly_score", sa.Numeric(8, 4), nullable=False),
        sa.Column("risk_score", sa.Numeric(8, 4), nullable=False),
        sa.Column("risk_level", sa.String(length=50), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_risk_scores_risk_level", "risk_scores", ["risk_level"])
    op.create_index("ix_risk_scores_transaction_id", "risk_scores", ["transaction_id"])

    op.create_table(
        "fraud_events",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("transaction_id", uuid_type, sa.ForeignKey("transactions.id"), nullable=False),
        sa.Column("risk_score_id", uuid_type, sa.ForeignKey("risk_scores.id"), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("amount_at_risk", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fraud_events_risk_score_id", "fraud_events", ["risk_score_id"])
    op.create_index("ix_fraud_events_transaction_id", "fraud_events", ["transaction_id"])

    op.create_table(
        "recovery_opportunities",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("transaction_id", uuid_type, sa.ForeignKey("transactions.id"), nullable=True),
        sa.Column("customer_id", uuid_type, sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("opportunity_type", sa.String(length=100), nullable=False),
        sa.Column("amount_at_risk", sa.Numeric(12, 2), nullable=False),
        sa.Column("recovery_probability", sa.Numeric(5, 4), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_recovery_opportunities_customer_id", "recovery_opportunities", ["customer_id"])
    op.create_index("ix_recovery_opportunities_status", "recovery_opportunities", ["status"])
    op.create_index("ix_recovery_opportunities_transaction_id", "recovery_opportunities", ["transaction_id"])

    op.create_table(
        "recovery_actions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("opportunity_id", uuid_type, sa.ForeignKey("recovery_opportunities.id"), nullable=False),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("action_status", sa.String(length=50), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_recovery_actions_opportunity_id", "recovery_actions", ["opportunity_id"])

    op.create_table(
        "revenue_events",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("merchant_id", uuid_type, sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("reference_id", sa.String(length=255), nullable=True),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
    )
    op.create_index("ix_revenue_events_event_timestamp", "revenue_events", ["event_timestamp"])
    op.create_index("ix_revenue_events_merchant_id", "revenue_events", ["merchant_id"])

    op.create_table(
        "policies",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("merchant_id", uuid_type, sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("policy_name", sa.String(length=255), nullable=False),
        sa.Column("policy_type", sa.String(length=100), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_policies_merchant_id", "policies", ["merchant_id"])

    op.create_table(
        "agent_decisions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("merchant_id", uuid_type, sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("transaction_id", uuid_type, sa.ForeignKey("transactions.id"), nullable=True),
        sa.Column("opportunity_id", uuid_type, sa.ForeignKey("recovery_opportunities.id"), nullable=True),
        sa.Column("decision_type", sa.String(length=100), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("policy_result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_decisions_merchant_id", "agent_decisions", ["merchant_id"])
    op.create_index("ix_agent_decisions_opportunity_id", "agent_decisions", ["opportunity_id"])
    op.create_index("ix_agent_decisions_transaction_id", "agent_decisions", ["transaction_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("merchant_id", uuid_type, sa.ForeignKey("merchants.id"), nullable=True),
        sa.Column("actor_type", sa.String(length=100), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("decision", sa.String(length=100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_merchant_id", "audit_logs", ["merchant_id"])

    op.create_table(
        "documents",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("merchant_id", uuid_type, sa.ForeignKey("merchants.id"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_merchant_id", "documents", ["merchant_id"])


def downgrade() -> None:
    op.drop_index("ix_documents_merchant_id", table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_audit_logs_merchant_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_agent_decisions_transaction_id", table_name="agent_decisions")
    op.drop_index("ix_agent_decisions_opportunity_id", table_name="agent_decisions")
    op.drop_index("ix_agent_decisions_merchant_id", table_name="agent_decisions")
    op.drop_table("agent_decisions")
    op.drop_index("ix_policies_merchant_id", table_name="policies")
    op.drop_table("policies")
    op.drop_index("ix_revenue_events_merchant_id", table_name="revenue_events")
    op.drop_index("ix_revenue_events_event_timestamp", table_name="revenue_events")
    op.drop_table("revenue_events")
    op.drop_index("ix_recovery_actions_opportunity_id", table_name="recovery_actions")
    op.drop_table("recovery_actions")
    op.drop_index("ix_recovery_opportunities_transaction_id", table_name="recovery_opportunities")
    op.drop_index("ix_recovery_opportunities_status", table_name="recovery_opportunities")
    op.drop_index("ix_recovery_opportunities_customer_id", table_name="recovery_opportunities")
    op.drop_table("recovery_opportunities")
    op.drop_index("ix_fraud_events_transaction_id", table_name="fraud_events")
    op.drop_index("ix_fraud_events_risk_score_id", table_name="fraud_events")
    op.drop_table("fraud_events")
    op.drop_index("ix_risk_scores_transaction_id", table_name="risk_scores")
    op.drop_index("ix_risk_scores_risk_level", table_name="risk_scores")
    op.drop_table("risk_scores")
    op.drop_index("ix_payment_attempts_transaction_id", table_name="payment_attempts")
    op.drop_table("payment_attempts")
    op.drop_index("ix_transactions_transaction_timestamp", table_name="transactions")
    op.drop_index("ix_transactions_status", table_name="transactions")
    op.drop_index("ix_transactions_merchant_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_customers_merchant_id", table_name="customers")
    op.drop_table("customers")
    op.drop_index("ix_merchants_email", table_name="merchants")
    op.drop_table("merchants")

