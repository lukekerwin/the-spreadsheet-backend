"""Migrate existing user subscriptions to new tables

Revision ID: 003_migrate_user_subscriptions
Revises: 002_seed_plans
Create Date: 2025-01-06

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_migrate_user_subscriptions"
down_revision: Union[str, None] = "002_seed_plans"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migrate existing active subscriptions from users table to subscriptions table
    # Only migrate users who have a stripe_subscription_id (actual subscribers)
    op.execute(
        sa.text(
            """
            INSERT INTO auth.subscriptions (
                id, user_id, plan_id, stripe_subscription_id, status,
                current_period_end, cancel_at_period_end, created_at, updated_at
            )
            SELECT
                gen_random_uuid(),
                u.id,
                p.id,
                u.stripe_subscription_id,
                u.subscription_status,
                u.subscription_current_period_end,
                u.subscription_cancel_at_period_end,
                NOW(),
                NOW()
            FROM auth.users u
            CROSS JOIN auth.plans p
            WHERE u.stripe_subscription_id IS NOT NULL
              AND u.subscription_tier = 'subscriber'
              AND p.features->>'premium_access' = 'true'
              AND p.plan_type = 'subscription'
            """
        )
    )

    # Migrate existing bidding package purchases from users table to purchases table
    op.execute(
        sa.text(
            """
            INSERT INTO auth.purchases (
                id, user_id, plan_id, status, amount_cents, currency,
                purchased_at, created_at, updated_at
            )
            SELECT
                gen_random_uuid(),
                u.id,
                p.id,
                'completed',
                p.price_cents,
                'usd',
                NOW(),
                NOW(),
                NOW()
            FROM auth.users u
            CROSS JOIN auth.plans p
            WHERE u.has_bidding_package = true
              AND p.features->>'bidding_package' = 'true'
              AND p.plan_type = 'one_time'
            """
        )
    )


def downgrade() -> None:
    # Remove migrated subscriptions and purchases
    # Note: This doesn't restore the original user fields since they're still there
    op.execute(sa.text("DELETE FROM auth.purchases"))
    op.execute(sa.text("DELETE FROM auth.subscriptions"))
