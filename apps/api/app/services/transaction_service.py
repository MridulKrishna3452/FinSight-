import hashlib
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import CategorizationSource, Category, TransactionType
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionFilters, TransactionUpdate
from app.services import alert_service, anomaly_service, categorization_service


def compute_dedup_hash(
    user_id: uuid.UUID, transaction_date: date, amount: Decimal, description: str
) -> str:
    raw = f"{user_id}|{transaction_date.isoformat()}|{amount}|{description.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def create_transaction(db: Session, user_id: uuid.UUID, payload: TransactionCreate) -> Transaction:
    category = payload.category
    categorization_source = CategorizationSource.USER_OVERRIDE
    if category is None:
        result = categorization_service.categorize(payload.merchant_name, payload.description)
        category = result.category
        categorization_source = result.source

    dedup_hash = compute_dedup_hash(
        user_id, payload.transaction_date, payload.amount, payload.description
    )

    transaction = Transaction(
        user_id=user_id,
        transaction_date=payload.transaction_date,
        merchant_name=payload.merchant_name,
        description=payload.description,
        amount=payload.amount,
        transaction_type=payload.transaction_type,
        category=category,
        categorization_source=categorization_source,
        payment_method=payload.payment_method,
        is_recurring=payload.is_recurring,
        dedup_hash=dedup_hash,
    )

    if payload.transaction_type == TransactionType.EXPENSE:
        anomaly = anomaly_service.score_transaction(
            db,
            user_id,
            float(payload.amount),
            category.value,
            payload.merchant_name,
            payload.transaction_date,
        )
        transaction.anomaly_score = Decimal(str(anomaly.score))
        transaction.is_suspicious = anomaly.is_suspicious
        transaction.anomaly_explanation = anomaly.explanation

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    if transaction.is_suspicious:
        alert_service.create_suspicious_transaction_alert(db, transaction)
    if transaction.transaction_type == TransactionType.EXPENSE:
        alert_service.check_budgets_for_transaction(db, user_id, transaction)

    return transaction


def update_transaction(
    db: Session, transaction: Transaction, payload: TransactionUpdate
) -> Transaction:
    data = payload.model_dump(exclude_unset=True)
    category_manually_set = "category" in data and data["category"] is not None

    for field, value in data.items():
        setattr(transaction, field, value)

    if category_manually_set:
        transaction.categorization_source = CategorizationSource.USER_OVERRIDE

    transaction.dedup_hash = compute_dedup_hash(
        transaction.user_id,
        transaction.transaction_date,
        transaction.amount,
        transaction.description,
    )

    db.commit()
    db.refresh(transaction)
    return transaction


def get_transaction_for_user(
    db: Session, transaction_id: uuid.UUID, user_id: uuid.UUID
) -> Transaction | None:
    return db.execute(
        select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id)
    ).scalar_one_or_none()


def delete_transaction(db: Session, transaction: Transaction) -> None:
    db.delete(transaction)
    db.commit()


def _apply_filters(stmt: Select, user_id: uuid.UUID, filters: TransactionFilters) -> Select:
    stmt = stmt.where(Transaction.user_id == user_id)

    if filters.search:
        like_pattern = f"%{filters.search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Transaction.merchant_name).like(like_pattern),
                func.lower(Transaction.description).like(like_pattern),
            )
        )
    if filters.category is not None:
        stmt = stmt.where(Transaction.category == filters.category)
    if filters.transaction_type is not None:
        stmt = stmt.where(Transaction.transaction_type == filters.transaction_type)
    if filters.is_suspicious is not None:
        stmt = stmt.where(Transaction.is_suspicious == filters.is_suspicious)
    if filters.date_from is not None:
        stmt = stmt.where(Transaction.transaction_date >= filters.date_from)
    if filters.date_to is not None:
        stmt = stmt.where(Transaction.transaction_date <= filters.date_to)

    return stmt


SORTABLE_COLUMNS = {
    "transaction_date": Transaction.transaction_date,
    "amount": Transaction.amount,
    "merchant_name": Transaction.merchant_name,
    "category": Transaction.category,
    "created_at": Transaction.created_at,
}


def list_transactions(
    db: Session, user_id: uuid.UUID, filters: TransactionFilters
) -> tuple[list[Transaction], int]:
    base_stmt = _apply_filters(select(Transaction), user_id, filters)

    count_stmt = _apply_filters(select(func.count(Transaction.id)), user_id, filters)
    total = db.execute(count_stmt).scalar_one()

    sort_column = SORTABLE_COLUMNS.get(filters.sort_by, Transaction.transaction_date)
    order = sort_column.desc() if filters.sort_dir == "desc" else sort_column.asc()
    stmt = (
        base_stmt.order_by(order)
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    )

    items = list(db.execute(stmt).scalars().all())
    return items, total


def list_all_for_export(
    db: Session, user_id: uuid.UUID, filters: TransactionFilters
) -> list[Transaction]:
    stmt = _apply_filters(select(Transaction), user_id, filters)
    sort_column = SORTABLE_COLUMNS.get(filters.sort_by, Transaction.transaction_date)
    order = sort_column.desc() if filters.sort_dir == "desc" else sort_column.asc()
    stmt = stmt.order_by(order)
    return list(db.execute(stmt).scalars().all())


ALL_CATEGORIES = [c.value for c in Category]
