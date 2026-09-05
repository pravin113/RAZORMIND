"""Add recovery outcomes table for Phase 6 learning and tracking.

Revision ID: 003_recovery_outcomes
Revises: 002_razorpay_webhook_events
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_recovery_outcomes"
down_revision: str | None = "002_razorpay_webhook_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid_type = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "recovery_outcomes",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("opportunity_id", uuid_type, sa.ForeignKey("recovery_opportunities.id"), nullable=False),
        sa.Column("merchant_id", uuid_type, sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("predicted_probability", sa.Numeric(5, 4), nullable=False),
        sa.Column("chosen_action", sa.String(length=100), nullable=False),
        sa.Column("policy_decision", sa.String(length=50), nullable=False),
        sa.Column("actual_result", sa.String(length=50), nullable=False),
        sa.Column("recovered_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("prediction_correctness", sa.Boolean(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_recovery_outcomes_opportunity_id", "recovery_outcomes", ["opportunity_id"])
    op.create_index("ix_recovery_outcomes_merchant_id", "recovery_outcomes", ["merchant_id"])
    op.create_index("ix_recovery_outcomes_created_at", "recovery_outcomes", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_recovery_outcomes_created_at", table_name="recovery_outcomes")
    op.drop_index("ix_recovery_outcomes_merchant_id", table_name="recovery_outcomes")
    op.drop_index("ix_recovery_outcomes_opportunity_id", table_name="recovery_outcomes")
    op.drop_table("recovery_outcomes")
