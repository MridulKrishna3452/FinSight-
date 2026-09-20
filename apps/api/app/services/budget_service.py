import calendar
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.budget import Budget
from app.models.enums import AlertSeverity, AlertType, TransactionType
from app.models.transaction import Transaction
from app.schemas.budget import BudgetProgress

WARNING_THRESHOLD = 0.80
DANGER_THRESHOLD = 0.90
FULL_THRESHOLD = 1.00


def month_spend(db: Session, user_id: uuid.UUID, budget: Budget) -> Decimal:
    _, last_day = calendar.monthrange(budget.year, budget.month)
    start = date(budget.year, budget.month, 1)
    end = date(budget.year, budget.month, last_day)

    stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= start,
        Transaction.transaction_date <= end,
    )
    if budget.category is not None:
        stmt = stmt.where(Transaction.category == budget.category)

    result = db.execute(stmt).scalar_one()
    return Decimal(str(result))


def status_for_percent(percent: float) -> str:
    if percent >= 90:
        return "red"
    if percent >= 70:
        return "yellow"
    return "green"


def to_progress(db: Session, user_id: uuid.UUID, budget: Budget) -> BudgetProgress:
    spent = month_spend(db, user_id, budget)
    remaining = budget.monthly_limit - spent
    percent = float(spent / budget.monthly_limit * 100) if budget.monthly_limit else 0.0

    return BudgetProgress(
        id=budget.id,
        name=budget.name,
        category=budget.category,
        monthly_limit=budget.monthly_limit,
        month=budget.month,
        year=budget.year,
        spent=spent,
        remaining=remaining,
        percent_consumed=round(percent, 1),
        status=status_for_percent(percent),
    )


def check_and_create_threshold_alerts(db: Session, user_id: uuid.UUID, budget: Budget) -> None:
    """Creates a budget-threshold alert the first time spend crosses 80/90/100%.
    Avoids duplicate alerts by checking for an existing unread alert for the
    same budget at the same threshold tier within the same month."""
    spent = month_spend(db, user_id, budget)
    percent = float(spent / budget.monthly_limit * 100) if budget.monthly_limit else 0.0

    tier: tuple[str, AlertSeverity] | None = None
    if percent >= 100:
        tier = ("100%", AlertSeverity.CRITICAL)
    elif percent >= 90:
        tier = ("90%", AlertSeverity.WARNING)
    elif percent >= 80:
        tier = ("80%", AlertSeverity.WARNING)

    if tier is None:
        return

    label, severity = tier
    title = f"{budget.name} budget at {label}"

    existing = db.execute(
        select(Alert).where(
            Alert.user_id == user_id,
            Alert.related_budget_id == budget.id,
            Alert.title == title,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return

    message = (
        f"You've spent {spent} of your {budget.monthly_limit} monthly budget for "
        f"{budget.name} ({percent:.0f}%)."
    )
    alert = Alert(
        user_id=user_id,
        alert_type=AlertType.BUDGET_THRESHOLD,
        severity=severity,
        title=title,
        message=message,
        related_budget_id=budget.id,
    )
    db.add(alert)
    db.commit()
