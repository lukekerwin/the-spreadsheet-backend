"""Add subscription tables

Revision ID: 001_add_subscription_tables
Revises:
Create Date: 2025-01-06

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_add_subscription_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create auth.plans table
    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stripe_price_id", sa.String(255), unique=True, nullable=False),
        sa.Column("stripe_product_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("plan_type", sa.String(20), nullable=False),
        sa.Column("billing_interval", sa.String(20), nullable=True),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="usd"),
        sa.Column("features", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="auth",
    )
    op.create_index(
        "idx_plans_stripe_price_id",
        "plans",
        ["stripe_price_id"],
        schema="auth",
    )

    # Create auth.subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.plans.id"),
            nullable=False,
        ),
        sa.Column("stripe_subscription_id", sa.String(255), unique=True, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "cancel_at_period_end", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_data", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="auth",
    )
    op.create_index(
        "idx_subscriptions_user_id",
        "subscriptions",
        ["user_id"],
        schema="auth",
    )
    op.create_index(
        "idx_subscriptions_status",
        "subscriptions",
        ["status"],
        schema="auth",
    )
    op.create_index(
        "idx_subscriptions_stripe_id",
        "subscriptions",
        ["stripe_subscription_id"],
        schema="auth",
    )
    op.create_index(
        "idx_subscriptions_user_active",
        "subscriptions",
        ["user_id", "status"],
        schema="auth",
    )

    # Create auth.purchases table
    op.create_table(
        "purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.plans.id"),
            nullable=False,
        ),
        sa.Column(
            "stripe_payment_intent_id", sa.String(255), unique=True, nullable=True
        ),
        sa.Column("stripe_checkout_session_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="usd"),
        sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_data", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="auth",
    )
    op.create_index(
        "idx_purchases_user_id",
        "purchases",
        ["user_id"],
        schema="auth",
    )
    op.create_index(
        "idx_purchases_status",
        "purchases",
        ["status"],
        schema="auth",
    )
    op.create_index(
        "idx_purchases_stripe_payment",
        "purchases",
        ["stripe_payment_intent_id"],
        schema="auth",
    )
    op.create_unique_constraint(
        "uq_user_plan_purchase",
        "purchases",
        ["user_id", "plan_id"],
        schema="auth",
    )

    # Create auth.payment_history table
    op.create_table(
        "payment_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.subscriptions.id"),
            nullable=True,
        ),
        sa.Column(
            "purchase_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.purchases.id"),
            nullable=True,
        ),
        sa.Column("stripe_invoice_id", sa.String(255), nullable=True),
        sa.Column("stripe_payment_intent_id", sa.String(255), nullable=True),
        sa.Column("stripe_charge_id", sa.String(255), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="usd"),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("refund_reason", sa.Text(), nullable=True),
        sa.Column("invoice_url", sa.Text(), nullable=True),
        sa.Column("receipt_url", sa.Text(), nullable=True),
        sa.Column("extra_data", postgresql.JSONB(), nullable=True),
        sa.Column(
            "event_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="auth",
    )
    op.create_index(
        "idx_payment_history_user_id",
        "payment_history",
        ["user_id"],
        schema="auth",
    )
    op.create_index(
        "idx_payment_history_subscription",
        "payment_history",
        ["subscription_id"],
        schema="auth",
    )
    op.create_index(
        "idx_payment_history_purchase",
        "payment_history",
        ["purchase_id"],
        schema="auth",
    )
    op.create_index(
        "idx_payment_history_event_at",
        "payment_history",
        ["event_at"],
        schema="auth",
    )
    op.create_index(
        "idx_payment_history_stripe_invoice",
        "payment_history",
        ["stripe_invoice_id"],
        schema="auth",
    )


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("payment_history", schema="auth")
    op.drop_table("purchases", schema="auth")
    op.drop_table("subscriptions", schema="auth")
    op.drop_table("plans", schema="auth")
