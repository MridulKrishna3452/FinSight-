import uuid

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.enums import AlertSeverity, AlertType
from app.models.transaction import Transaction


def create_suspicious_transaction_alert(db: Session, transaction: Transaction) -> Alert:
    message = transaction.anomaly_explanation or (
        "This transaction was flagged as a risk indicator based on your spending patterns."
    )
    alert = Alert(
        user_id=transaction.user_id,
        alert_type=AlertType.SUSPICIOUS_TRANSACTION,
        severity=AlertSeverity.WARNING,
        title=f"Suspicious transaction: {transaction.merchant_name}",
        message=f"{message} (Risk indicator, not confirmed fraud.)",
        related_transaction_id=transaction.id,
    )
    db.add(alert)
    db.commit()
    return alert


def check_budgets_for_transaction(
    db: Session, user_id: uuid.UUID, transaction: Transaction
) -> None:
    from sqlalchemy import select

    from app.models.budget import Budget
    from app.services import budget_service

    stmt = select(Budget).where(
        Budget.user_id == user_id,
        Budget.month == transaction.transaction_date.month,
        Budget.year == transaction.transaction_date.year,
    )
    budgets = db.execute(stmt).scalars().all()
    for budget in budgets:
        if budget.category is None or budget.category == transaction.category:
            budget_service.check_and_create_threshold_alerts(db, user_id, budget)
