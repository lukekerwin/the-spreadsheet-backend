"""Seed initial plans

Revision ID: 002_seed_plans
Revises: 001_add_subscription_tables
Create Date: 2025-01-06

"""

import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_seed_plans"
down_revision: Union[str, None] = "001_add_subscription_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get price IDs from environment (with fallback to dev values)
    subscription_price_id = os.environ.get(
        "STRIPE_PRICE_ID", "price_1SeNKDGEL9zj1vFFO5kgyfPy"
    )
    bidding_package_price_id = os.environ.get(
        "STRIPE_BIDDING_PACKAGE_PRICE_ID", "price_1SeNJLGEL9zj1vFFxlhSX8mc"
    )

    # Insert Premium Subscription plan
    op.execute(
        sa.text(
            """
            INSERT INTO auth.plans (
                id, stripe_price_id, stripe_product_id, name, description,
                plan_type, billing_interval, price_cents, currency, features,
                is_active, sort_order
            ) VALUES (
                gen_random_uuid(),
                :subscription_price_id,
                'prod_premium_subscription',
                'Premium Subscription',
                'Full access to real-time hockey analytics data',
                'subscription',
                'month',
                999,
                'usd',
                '{"premium_access": true, "real_time_data": true}'::jsonb,
                true,
                1
            )
            """
        ).bindparams(subscription_price_id=subscription_price_id)
    )

    # Insert Bidding Package plan (one-time purchase)
    op.execute(
        sa.text(
            """
            INSERT INTO auth.plans (
                id, stripe_price_id, stripe_product_id, name, description,
                plan_type, billing_interval, price_cents, currency, features,
                is_active, sort_order
            ) VALUES (
                gen_random_uuid(),
                :bidding_package_price_id,
                'prod_bidding_package',
                'Bidding Package',
                'Access to bidding analytics and draft tools',
                'one_time',
                NULL,
                1999,
                'usd',
                '{"bidding_package": true}'::jsonb,
                true,
                2
            )
            """
        ).bindparams(bidding_package_price_id=bidding_package_price_id)
    )


def downgrade() -> None:
    # Remove seeded plans
    op.execute(
        sa.text("DELETE FROM auth.plans WHERE name IN ('Premium Subscription', 'Bidding Package')")
    )
