#!/usr/bin/env python3
"""Seeds a demo user with 6+ months of realistic synthetic Indian transaction
data, budgets, recurring subscriptions, and intentionally suspicious
transactions -- enough for every dashboard chart, budget, and forecast to
look meaningful out of the box.

Amounts are calibrated against total simulated income rather than drawn from
independent fixed ranges: fixed costs (rent, subscriptions, SIP) and
suspicious transactions are sized as a share of income, and variable
day-to-day spending is generated with relative weights per category and then
scaled to fill whatever income remains after a target expense ratio. This
keeps the overall balance and savings rate realistic (positive, in the
15-25% range) regardless of how the random draws land, instead of risking a
wildly negative balance from unconstrained random amounts.

Usage:
    python -m app.seed.seed_demo_data
"""

import random
import sys
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.budget import Budget  # noqa: E402
from app.models.enums import Category, TransactionType  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.transaction import TransactionCreate  # noqa: E402
from app.services import transaction_service  # noqa: E402

DEMO_EMAIL = "demo@finsight.app"
DEMO_PASSWORD = "Demo@12345"
DEMO_NAME = "Demo User"

# (merchant, relative weight, payment methods). Weight reflects how often AND
# how much a merchant typically costs relative to others -- e.g. a grocery
# run is both less frequent and pricier per-visit than a coffee run.
VARIABLE_MERCHANTS: list[tuple[str, float]] = [
    ("Swiggy", 1.0),
    ("Zomato", 1.0),
    ("Starbucks", 0.6),
    ("Uber", 0.7),
    ("Ola", 0.6),
    ("Indian Oil Petrol Pump", 1.8),
    ("Amazon", 2.2),
    ("Flipkart", 2.0),
    ("Myntra", 1.6),
    ("BookMyShow", 0.9),
    ("BigBasket", 2.4),
    ("DMart", 2.0),
    ("Apollo Pharmacy", 1.1),
]
# Rare, big-ticket merchant -- appears far less often than the list above.
RARE_MERCHANT = ("MakeMyTrip", 6.0)
RARE_MERCHANT_PROBABILITY = 0.05

RECURRING_SUBSCRIPTIONS: list[tuple[str, int, Decimal]] = [
    ("Netflix", 5, Decimal("499")),
    ("Spotify", 5, Decimal("119")),
    ("Jio Fiber", 7, Decimal("999")),
    ("Airtel Postpaid", 10, Decimal("599")),
]

SUSPICIOUS_MERCHANTS = ["Unknown Merchant XYZ", "Luxury Electronics Store", "Overseas Purchase Co"]
SUSPICIOUS_COUNT = 6
SUSPICIOUS_INCOME_SHARE = 0.10  # ~10% of total income, spread across the count above

RENT_INCOME_SHARE = 0.21
SIP_INCOME_SHARE = 0.07
TARGET_EXPENSE_RATIO = 0.80  # ~20% overall savings rate

BUDGET_CATEGORIES: list[tuple[Category, Decimal]] = [
    (Category.GROCERIES, Decimal("8000")),
    (Category.DINING, Decimal("6000")),
    (Category.TRANSPORT, Decimal("4000")),
    (Category.SHOPPING, Decimal("10000")),
    (Category.ENTERTAINMENT, Decimal("2000")),
    (Category.UTILITIES, Decimal("2500")),
]


def _round_rupees(amount: float) -> Decimal:
    return Decimal(str(max(amount, 10))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _get_or_create_demo_user(db: Session) -> User:
    user = db.execute(select(User).where(User.email == DEMO_EMAIL)).scalar_one_or_none()
    if user is not None:
        return user
    user = User(email=DEMO_EMAIL, hashed_password=hash_password(DEMO_PASSWORD), full_name=DEMO_NAME)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _clear_existing_data(db: Session, user_id) -> None:
    from app.models.alert import Alert
    from app.models.import_job import ImportJob
    from app.models.transaction import Transaction

    db.query(Alert).filter(Alert.user_id == user_id).delete()
    db.query(Transaction).filter(Transaction.user_id == user_id).delete()
    db.query(ImportJob).filter(ImportJob.user_id == user_id).delete()
    db.query(Budget).filter(Budget.user_id == user_id).delete()
    db.commit()


def _create_budgets(db: Session, user_id, today: date) -> None:
    for category, limit in BUDGET_CATEGORIES:
        db.add(
            Budget(
                user_id=user_id,
                category=category,
                name=f"{category.value} Budget",
                monthly_limit=limit,
                month=today.month,
                year=today.year,
            )
        )
    db.commit()


def _generate_transaction_rows(months: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    today = date.today()
    start = today - timedelta(days=30 * months)
    total_days = (today - start).days

    rows: list[dict] = []
    total_income = Decimal("0")

    # --- Income (salary, 1st of each month) ---
    day = start
    while day <= today:
        if day.day == 1:
            salary = Decimal(rng.randint(65000, 92000))
            total_income += salary
            rows.append(
                {
                    "date": day,
                    "merchant": "Acme Corp",
                    "description": "SALARY CREDIT",
                    "amount": salary,
                    "type": TransactionType.INCOME,
                    "payment_method": "Bank Transfer",
                    "recurring": True,
                }
            )
        day += timedelta(days=1)

    if total_income == 0:
        total_income = Decimal("75000")  # guard against a degenerate 0-month run

    # --- Fixed costs sized as a share of total income ---
    n_months = max(months, 1)
    rent_total = float(total_income) * RENT_INCOME_SHARE
    sip_total = float(total_income) * SIP_INCOME_SHARE

    day = start
    while day <= today:
        if day.day == 3:
            rows.append(
                {
                    "date": day,
                    "merchant": "Landlord - Rent",
                    "description": "MONTHLY RENT",
                    "amount": _round_rupees(rent_total / n_months * rng.uniform(0.9, 1.1)),
                    "type": TransactionType.EXPENSE,
                    "payment_method": "Net Banking",
                    "recurring": True,
                }
            )
        if day.day == 12:
            rows.append(
                {
                    "date": day,
                    "merchant": "Zerodha",
                    "description": "SIP MUTUAL FUND",
                    "amount": _round_rupees(sip_total / n_months * rng.uniform(0.85, 1.15)),
                    "type": TransactionType.EXPENSE,
                    "payment_method": "Net Banking",
                    "recurring": True,
                }
            )
        for merchant, sub_day, amount in RECURRING_SUBSCRIPTIONS:
            if day.day == sub_day:
                rows.append(
                    {
                        "date": day,
                        "merchant": merchant,
                        "description": f"{merchant.upper()} SUBSCRIPTION",
                        "amount": amount,
                        "type": TransactionType.EXPENSE,
                        "payment_method": "Credit Card",
                        "recurring": True,
                    }
                )
        day += timedelta(days=1)

    fixed_total = sum(
        (float(r["amount"]) for r in rows if r["type"] == TransactionType.EXPENSE), 0.0
    )

    # --- Suspicious/anomalous transactions, sized as a moderate income share ---
    suspicious_budget = float(total_income) * SUSPICIOUS_INCOME_SHARE
    suspicious_weights = [rng.uniform(0.6, 1.6) for _ in range(SUSPICIOUS_COUNT)]
    weight_sum = sum(suspicious_weights)
    for weight in suspicious_weights:
        odd_day = start + timedelta(days=rng.randint(0, total_days))
        merchant = rng.choice(SUSPICIOUS_MERCHANTS + ["Amazon", "Flipkart"])
        amount = _round_rupees(max(suspicious_budget * weight / weight_sum, 8000))
        rows.append(
            {
                "date": odd_day,
                "merchant": merchant,
                "description": f"{merchant.upper()} LARGE PURCHASE",
                "amount": amount,
                "type": TransactionType.EXPENSE,
                "payment_method": "Credit Card",
                "recurring": False,
            }
        )
    # Actual sum may exceed suspicious_budget slightly due to the 8,000 floor
    # on very small weight shares -- use the real sum for accurate calibration.
    suspicious_total = float(
        sum(
            _round_rupees(max(suspicious_budget * w / weight_sum, 8000)) for w in suspicious_weights
        )
    )

    # --- Variable day-to-day spending: generate weighted templates, then
    # scale so their total fills whatever income remains after the target
    # expense ratio, given fixed + suspicious costs already committed. ---
    variable_templates: list[dict] = []
    day = start
    while day <= today:
        daily_count = rng.randint(4, 8)
        for _ in range(daily_count):
            if rng.random() < RARE_MERCHANT_PROBABILITY:
                merchant, weight = RARE_MERCHANT
            else:
                merchant, weight = rng.choice(VARIABLE_MERCHANTS)
            jittered_weight = weight * rng.uniform(0.6, 1.5)
            variable_templates.append(
                {
                    "date": day,
                    "merchant": merchant,
                    "description": f"{merchant.upper()} PURCHASE",
                    "weight": jittered_weight,
                    "type": TransactionType.EXPENSE,
                    "payment_method": rng.choice(
                        ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash"]
                    ),
                    "recurring": False,
                }
            )
        day += timedelta(days=1)

    target_total_expense = float(total_income) * TARGET_EXPENSE_RATIO
    remaining_budget = max(
        target_total_expense - fixed_total - suspicious_total, float(total_income) * 0.08
    )
    weight_total = sum(t["weight"] for t in variable_templates) or 1.0
    scale = remaining_budget / weight_total

    for template in variable_templates:
        amount = _round_rupees(template.pop("weight") * scale)
        template["amount"] = amount
        rows.append(template)

    rows.sort(key=lambda r: r["date"])
    return rows


def seed(months: int = 6, seed_value: int = 42) -> None:
    db = SessionLocal()
    try:
        user = _get_or_create_demo_user(db)
        _clear_existing_data(db, user.id)
        _create_budgets(db, user.id, date.today())

        rows = _generate_transaction_rows(months, seed_value)
        print(f"Generating {len(rows)} transactions for {DEMO_EMAIL}...")

        for i, row in enumerate(rows, start=1):
            payload = TransactionCreate(
                transaction_date=row["date"],
                merchant_name=row["merchant"],
                description=row["description"],
                amount=row["amount"],
                transaction_type=row["type"],
                payment_method=row["payment_method"],
                is_recurring=row["recurring"],
            )
            transaction_service.create_transaction(db, user.id, payload)
            if i % 200 == 0:
                print(f"  ...{i}/{len(rows)} transactions created")

        print(f"Done. Seeded {len(rows)} transactions, {len(BUDGET_CATEGORIES)} budgets.")
        print(f"Demo login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
