#!/usr/bin/env python3
"""Generates a realistic synthetic Indian personal-finance transaction CSV for
demoing FinSight's CSV import flow. Pure stdlib (no pandas dependency) so it
can run anywhere. Not connected to any real bank; all data is fabricated.

Usage:
    python synthetic_transactions_generator.py --months 3 --out sample_transactions.csv
"""

import argparse
import csv
import random
from datetime import date, timedelta

MERCHANTS: list[tuple[str, str, tuple[int, int]]] = [
    ("Swiggy", "Dining", (150, 800)),
    ("Zomato", "Dining", (150, 900)),
    ("Starbucks", "Dining", (250, 700)),
    ("Uber", "Transport", (80, 600)),
    ("Ola", "Transport", (80, 550)),
    ("Indian Oil Petrol Pump", "Transport", (500, 3000)),
    ("Amazon", "Shopping", (300, 5000)),
    ("Flipkart", "Shopping", (300, 6000)),
    ("Myntra", "Shopping", (500, 4000)),
    ("Netflix", "Entertainment", (199, 649)),
    ("Spotify", "Entertainment", (119, 199)),
    ("BookMyShow", "Entertainment", (200, 1200)),
    ("BigBasket", "Groceries", (500, 3500)),
    ("DMart", "Groceries", (400, 3000)),
    ("Apollo Pharmacy", "Healthcare", (150, 2500)),
    ("Airtel Postpaid", "Utilities", (399, 999)),
    ("Jio Fiber", "Utilities", (699, 1499)),
    ("Electricity Board", "Utilities", (800, 4500)),
    ("MakeMyTrip", "Travel", (2000, 25000)),
    ("IRCTC", "Travel", (300, 3500)),
    ("LIC Premium", "Insurance", (1500, 8000)),
    ("Zerodha", "Investments", (1000, 20000)),
    ("Acme Corp", "Salary", (60000, 95000)),
    ("Landlord - Rent", "Housing", (12000, 28000)),
]

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash"]


def generate_rows(months: int, seed: int = 42) -> list[dict[str, str]]:
    rng = random.Random(seed)
    rows: list[dict[str, str]] = []
    today = date.today()
    start = today - timedelta(days=30 * months)

    day = start
    while day <= today:
        # Salary on the 1st of each month
        if day.day == 1:
            merchant, category, amt_range = ("Acme Corp", "Salary", (60000, 95000))
            rows.append(
                _row(day, merchant, "SALARY CREDIT", rng.randint(*amt_range), "income", "Bank Transfer")
            )
        # Rent on the 3rd
        if day.day == 3:
            rows.append(
                _row(day, "Landlord - Rent", "MONTHLY RENT", rng.randint(12000, 20000), "expense", "Net Banking")
            )
        # 2-5 random daily transactions
        for _ in range(rng.randint(0, 3)):
            merchant, category, amt_range = rng.choice(
                [m for m in MERCHANTS if m[1] not in ("Salary", "Housing")]
            )
            amount = rng.randint(*amt_range)
            payment_method = rng.choice(PAYMENT_METHODS)
            desc = f"{merchant.upper()} PURCHASE"
            rows.append(_row(day, merchant, desc, amount, "expense", payment_method))
        day += timedelta(days=1)

    # Sprinkle a handful of intentionally unusual/suspicious transactions
    for _ in range(max(1, months)):
        odd_day = start + timedelta(days=rng.randint(0, (today - start).days))
        merchant = rng.choice(["Unknown Merchant XYZ", "Amazon", "Flipkart"])
        amount = rng.randint(40000, 150000)
        rows.append(
            _row(odd_day, merchant, f"{merchant.upper()} LARGE PURCHASE", amount, "expense", "Credit Card")
        )

    rows.sort(key=lambda r: r["date"])
    return rows


def _row(day: date, merchant: str, desc: str, amount: int, txn_type: str, payment_method: str) -> dict[str, str]:
    return {
        "date": day.isoformat(),
        "description": desc,
        "amount": str(amount) if txn_type == "income" else str(-amount),
        "type": txn_type,
        "merchant": merchant,
        "payment_method": payment_method,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--months", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="sample_transactions.csv")
    args = parser.parse_args()

    rows = generate_rows(args.months, args.seed)
    fieldnames = ["date", "description", "amount", "type", "merchant", "payment_method"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
