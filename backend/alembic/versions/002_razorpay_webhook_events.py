"""Add Razorpay webhook event storage.

Revision ID: 002_razorpay_webhook_events
Revises: 001_initial_database_schema
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_razorpay_webhook_events"
down_revision: str | None = "001_initial_database_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


uuid_type = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_index("ix_transactions_razorpay_order_id", "transactions", ["razorpay_order_id"])
    op.create_index("ix_transactions_razorpay_payment_id", "transactions", ["razorpay_payment_id"], unique=True)
    op.create_table(
        "webhook_events",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("event_id", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("signature_verified", sa.Boolean(), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_webhook_events_event_id", "webhook_events", ["event_id"], unique=True)
    op.create_index("ix_webhook_events_event_type", "webhook_events", ["event_type"])
    op.create_index("ix_webhook_events_received_at", "webhook_events", ["received_at"])


def downgrade() -> None:
    op.drop_index("ix_webhook_events_received_at", table_name="webhook_events")
    op.drop_index("ix_webhook_events_event_type", table_name="webhook_events")
    op.drop_index("ix_webhook_events_event_id", table_name="webhook_events")
    op.drop_table("webhook_events")
    op.drop_index("ix_transactions_razorpay_payment_id", table_name="transactions")
    op.drop_index("ix_transactions_razorpay_order_id", table_name="transactions")

