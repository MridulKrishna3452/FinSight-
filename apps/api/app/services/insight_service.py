"""Analytics + deterministic "AI-style" insight generation.

No paid LLM API is required: `generate_insight_cards` builds human-readable
insight cards purely from analytics computed over the user's own transactions
(month-over-month deltas, budget pace, subscription totals, savings-rate
trend). An `LLMProvider` protocol is defined below so a real LLM can later be
plugged in to rephrase/enrich these cards -- the app is fully functional
without one (`NullLLMProvider` is the default and does nothing).
"""

import calendar
import uuid
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.enums import Category, TransactionType
from app.models.transaction import Transaction
from app.schemas.insight import (
    CategorySpend,
    DailySpendPoint,
    DashboardSummary,
    InsightCard,
    MonthlySummaryItem,
    RecurringExpense,
    TopMerchant,
)
from app.services import budget_service


class LLMProvider(Protocol):
    def enrich(self, cards: list[InsightCard]) -> list[InsightCard]: ...


class NullLLMProvider:
    """Default no-op provider so FinSight works with zero external API keys."""

    def enrich(self, cards: list[InsightCard]) -> list[InsightCard]:
        return cards


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    _, last_day = calendar.monthrange(year, month)
    return date(year, month, 1), date(year, month, last_day)


def _sum_for_month(
    db: Session, user_id: uuid.UUID, year: int, month: int, txn_type: TransactionType
) -> Decimal:
    start, end = _month_bounds(year, month)
    result = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == txn_type,
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
        )
    ).scalar_one()
    return Decimal(str(result))


def dashboard_summary(db: Session, user_id: uuid.UUID, today: date) -> DashboardSummary:
    income = _sum_for_month(db, user_id, today.year, today.month, TransactionType.INCOME)
    expense = _sum_for_month(db, user_id, today.year, today.month, TransactionType.EXPENSE)

    total_income = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id, Transaction.transaction_type == TransactionType.INCOME
        )
    ).scalar_one()
    total_expense = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id, Transaction.transaction_type == TransactionType.EXPENSE
        )
    ).scalar_one()
    balance = Decimal(str(total_income)) - Decimal(str(total_expense))

    savings_rate = float((income - expense) / income * 100) if income > 0 else 0.0
    txn_count = db.execute(
        select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
    ).scalar_one()

    return DashboardSummary(
        balance=balance,
        monthly_income=income,
        monthly_expense=expense,
        savings_rate=round(savings_rate, 1),
        transaction_count=txn_count,
    )


def spending_by_category(
    db: Session, user_id: uuid.UUID, year: int | None = None, month: int | None = None
) -> list[CategorySpend]:
    stmt = select(
        Transaction.category, func.sum(Transaction.amount), func.count(Transaction.id)
    ).where(Transaction.user_id == user_id, Transaction.transaction_type == TransactionType.EXPENSE)

    if year is not None and month is not None:
        start, end = _month_bounds(year, month)
        stmt = stmt.where(
            Transaction.transaction_date >= start, Transaction.transaction_date <= end
        )

    stmt = stmt.group_by(Transaction.category)
    rows = db.execute(stmt).all()

    total = sum(float(r[1]) for r in rows) or 1.0
    return sorted(
        [
            CategorySpend(
                category=category.value,
                total=Decimal(str(amount)),
                percent=round(float(amount) / total * 100, 1),
                transaction_count=count,
            )
            for category, amount, count in rows
        ],
        key=lambda c: c.total,
        reverse=True,
    )


def monthly_summary(db: Session, user_id: uuid.UUID, months: int = 6) -> list[MonthlySummaryItem]:
    rows = db.execute(
        select(
            func.date_trunc("month", Transaction.transaction_date).label("month"),
            Transaction.transaction_type,
            func.sum(Transaction.amount),
        )
        .where(Transaction.user_id == user_id)
        .group_by("month", Transaction.transaction_type)
        .order_by("month")
    ).all()

    by_month: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"income": Decimal(0), "expense": Decimal(0)}
    )
    for month_dt, txn_type, total in rows:
        key = month_dt.strftime("%Y-%m")
        by_month[key][txn_type.value] = Decimal(str(total))

    items = [
        MonthlySummaryItem(month=key, income=vals["income"], expense=vals["expense"])
        for key, vals in sorted(by_month.items())
    ]
    return items[-months:]


def daily_spending_trend(db: Session, user_id: uuid.UUID, days: int = 30) -> list[DailySpendPoint]:
    rows = db.execute(
        select(Transaction.transaction_date, func.sum(Transaction.amount))
        .where(
            Transaction.user_id == user_id, Transaction.transaction_type == TransactionType.EXPENSE
        )
        .group_by(Transaction.transaction_date)
        .order_by(Transaction.transaction_date.desc())
        .limit(days)
    ).all()
    return sorted(
        [DailySpendPoint(date=d, amount=Decimal(str(total))) for d, total in rows],
        key=lambda p: p.date,
    )


def top_merchants(db: Session, user_id: uuid.UUID, limit: int = 10) -> list[TopMerchant]:
    rows = db.execute(
        select(
            Transaction.merchant_name,
            Transaction.category,
            func.sum(Transaction.amount),
            func.count(Transaction.id),
        )
        .where(
            Transaction.user_id == user_id, Transaction.transaction_type == TransactionType.EXPENSE
        )
        .group_by(Transaction.merchant_name, Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
    ).all()
    return [
        TopMerchant(
            merchant_name=name,
            total=Decimal(str(total)),
            transaction_count=count,
            category=category.value,
        )
        for name, category, total, count in rows
    ]


def recurring_expenses(db: Session, user_id: uuid.UUID) -> list[RecurringExpense]:
    rows = db.execute(
        select(
            Transaction.merchant_name,
            Transaction.category,
            func.avg(Transaction.amount),
            func.count(Transaction.id),
            func.max(Transaction.transaction_date),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.is_recurring.is_(True),
        )
        .group_by(Transaction.merchant_name, Transaction.category)
        .order_by(func.avg(Transaction.amount).desc())
    ).all()
    return [
        RecurringExpense(
            merchant_name=name,
            category=category.value,
            average_amount=Decimal(str(round(float(avg_amt), 2))),
            occurrences=count,
            last_date=last_date,
        )
        for name, category, avg_amt, count, last_date in rows
    ]


def _prev_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def generate_insight_cards(
    db: Session, user_id: uuid.UUID, today: date, llm: LLMProvider | None = None
) -> list[InsightCard]:
    llm = llm or NullLLMProvider()
    cards: list[InsightCard] = []

    prev_year, prev_month = _prev_month(today.year, today.month)
    current_by_cat = {
        c.category: c.total for c in spending_by_category(db, user_id, today.year, today.month)
    }
    prev_by_cat = {
        c.category: c.total for c in spending_by_category(db, user_id, prev_year, prev_month)
    }

    for category, current_total in current_by_cat.items():
        prev_total = prev_by_cat.get(category)
        if prev_total and prev_total > 0:
            change_pct = float((current_total - prev_total) / prev_total * 100)
            if abs(change_pct) >= 15:
                direction = "higher" if change_pct > 0 else "lower"
                severity = "warning" if change_pct > 0 else "positive"
                cards.append(
                    InsightCard(
                        id=f"category-trend-{category}",
                        severity=severity,
                        title=f"{category} spending {direction}",
                        message=(
                            f"{category} spending is {abs(change_pct):.0f}% {direction} "
                            "than last month."
                        ),
                    )
                )

    budgets = list(
        db.execute(
            select(Budget).where(
                Budget.user_id == user_id, Budget.month == today.month, Budget.year == today.year
            )
        )
        .scalars()
        .all()
    )
    for budget in budgets:
        progress = budget_service.to_progress(db, user_id, budget)
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        days_elapsed = max(today.day, 1)
        projected_total = float(progress.spent) / days_elapsed * days_in_month
        if projected_total > float(budget.monthly_limit):
            overage = projected_total - float(budget.monthly_limit)
            cards.append(
                InsightCard(
                    id=f"budget-projection-{budget.id}",
                    severity="warning",
                    title=f"Projected to exceed {budget.name} budget",
                    message=(
                        f"You are projected to exceed your {budget.name} budget by "
                        f"₹{overage:,.0f} based on spending so far this month."
                    ),
                )
            )

    recurring = recurring_expenses(db, user_id)
    if len(recurring) >= 2:
        subscription_total = sum(float(r.average_amount) for r in recurring)
        cards.append(
            InsightCard(
                id="recurring-total",
                severity="info",
                title="Recurring subscriptions",
                message=f"{len(recurring)} subscriptions total ₹{subscription_total:,.0f}/month.",
            )
        )

    current_summary = dashboard_summary(db, user_id, today)
    prev_income = _sum_for_month(db, user_id, prev_year, prev_month, TransactionType.INCOME)
    prev_expense = _sum_for_month(db, user_id, prev_year, prev_month, TransactionType.EXPENSE)
    prev_savings_rate = (
        float((prev_income - prev_expense) / prev_income * 100) if prev_income > 0 else None
    )

    if prev_savings_rate is not None and abs(current_summary.savings_rate - prev_savings_rate) >= 3:
        direction = "rose" if current_summary.savings_rate > prev_savings_rate else "fell"
        severity = "positive" if current_summary.savings_rate > prev_savings_rate else "warning"
        cards.append(
            InsightCard(
                id="savings-rate-trend",
                severity=severity,
                title=f"Savings rate {direction}",
                message=(
                    f"Your savings rate {direction} from {prev_savings_rate:.0f}% to "
                    f"{current_summary.savings_rate:.0f}%."
                ),
            )
        )

    if not cards:
        cards.append(
            InsightCard(
                id="no-notable-changes",
                severity="info",
                title="Spending looks steady",
                message="No significant changes detected in your spending patterns this month.",
            )
        )

    return llm.enrich(cards)


ALL_CATEGORY_VALUES = [c.value for c in Category]
