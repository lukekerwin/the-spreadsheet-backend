"""Seed the Manager Tools subscription plan.

Creates the Stripe product + monthly price (unless --price-id is given)
and inserts the corresponding Plan row in auth.plans.

Usage:
    # Create Stripe product/price and seed the plan ($10/mo default)
    python scripts/seed_manager_tools_plan.py

    # Use an existing Stripe price (created in the dashboard)
    python scripts/seed_manager_tools_plan.py --price-id price_xxx --product-id prod_xxx

    # Custom price
    python scripts/seed_manager_tools_plan.py --price-cents 1000
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Make `app` importable when run from the backend root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import stripe  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.database.session import AsyncSessionLocal  # noqa: E402
from app.models.subscriptions import Plan  # noqa: E402

PLAN_NAME = "Manager Tools"
PLAN_DESCRIPTION = (
    "The GM toolkit: contract values, trade analyzer, depth charts, "
    "and opponent scouting. Includes full Subscriber premium access."
)
FEATURES = {"manager_tools": True, "premium_access": True}


def create_stripe_product_and_price(price_cents: int) -> tuple[str, str]:
    """Create the Stripe product and monthly price, returning (product_id, price_id)."""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if not stripe.api_key:
        raise SystemExit("STRIPE_SECRET_KEY is not set; pass --price-id/--product-id instead.")

    product = stripe.Product.create(name=PLAN_NAME, description=PLAN_DESCRIPTION)
    price = stripe.Price.create(
        product=product.id,
        unit_amount=price_cents,
        currency="usd",
        recurring={"interval": "month"},
    )
    return product.id, price.id


async def seed_plan(product_id: str, price_id: str, price_cents: int) -> None:
    """Insert (or update) the Manager Tools plan row."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Plan).where(Plan.stripe_price_id == price_id))
        existing = result.scalar_one_or_none()
        if existing:
            existing.name = PLAN_NAME
            existing.description = PLAN_DESCRIPTION
            existing.features = FEATURES
            existing.price_cents = price_cents
            existing.is_active = True
            session.add(existing)
            await session.commit()
            print(f"Updated existing plan {existing.id} for price {price_id}")
            return

        plan = Plan(
            stripe_price_id=price_id,
            stripe_product_id=product_id,
            name=PLAN_NAME,
            description=PLAN_DESCRIPTION,
            plan_type="subscription",
            billing_interval="month",
            price_cents=price_cents,
            currency="usd",
            features=FEATURES,
            is_active=True,
            sort_order=10,
        )
        session.add(plan)
        await session.commit()
        print(f"Created plan {plan.id} (price {price_id}, ${price_cents / 100:.2f}/mo)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Manager Tools subscription plan")
    parser.add_argument("--price-id", help="Existing Stripe price ID (skips Stripe creation)")
    parser.add_argument("--product-id", help="Existing Stripe product ID (required with --price-id)")
    parser.add_argument("--price-cents", type=int, default=1000, help="Monthly price in cents (default 1000)")
    args = parser.parse_args()

    if args.price_id:
        if not args.product_id:
            raise SystemExit("--product-id is required when using --price-id")
        product_id, price_id = args.product_id, args.price_id
    else:
        product_id, price_id = create_stripe_product_and_price(args.price_cents)
        print(f"Created Stripe product {product_id} and price {price_id}")

    asyncio.run(seed_plan(product_id, price_id, args.price_cents))
    print("Done. Set STRIPE_MANAGER_TOOLS_PRICE_ID in .env as a fallback:")
    print(f"  STRIPE_MANAGER_TOOLS_PRICE_ID={price_id}")


if __name__ == "__main__":
    main()
