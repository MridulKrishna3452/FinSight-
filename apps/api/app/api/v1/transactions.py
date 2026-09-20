import csv
import io
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.enums import Category, TransactionType
from app.models.user import User
from app.schemas.common import Page
from app.schemas.transaction import (
    TransactionCreate,
    TransactionFilters,
    TransactionRead,
    TransactionUpdate,
)
from app.services import transaction_service

router = APIRouter()


@router.get("", response_model=Page[TransactionRead])
def list_transactions(
    search: str | None = None,
    category: Category | None = None,
    transaction_type: TransactionType | None = None,
    is_suspicious: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: str = "transaction_date",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 25,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[TransactionRead]:
    filters = TransactionFilters(
        search=search,
        category=category,
        transaction_type=transaction_type,
        is_suspicious=is_suspicious,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
    items, total = transaction_service.list_transactions(db, current_user.id, filters)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return Page(
        items=[TransactionRead.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/export")
def export_transactions(
    search: str | None = None,
    category: Category | None = None,
    transaction_type: TransactionType | None = None,
    is_suspicious: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    filters = TransactionFilters(
        search=search,
        category=category,
        transaction_type=transaction_type,
        is_suspicious=is_suspicious,
        date_from=date_from,
        date_to=date_to,
        page=1,
        page_size=10_000,
    )
    items = transaction_service.list_all_for_export(db, current_user.id, filters)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "date",
            "merchant",
            "description",
            "amount",
            "type",
            "category",
            "payment_method",
            "is_recurring",
            "is_suspicious",
            "anomaly_score",
        ]
    )
    for t in items:
        writer.writerow(
            [
                t.transaction_date.isoformat(),
                t.merchant_name,
                t.description,
                t.amount,
                t.transaction_type.value,
                t.category.value,
                t.payment_method,
                t.is_recurring,
                t.is_suspicious,
                t.anomaly_score,
            ]
        )
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=finsight_transactions.csv"},
    )


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    transaction = transaction_service.create_transaction(db, current_user.id, payload)
    return TransactionRead.model_validate(transaction)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    transaction = transaction_service.get_transaction_for_user(db, transaction_id, current_user.id)
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return TransactionRead.model_validate(transaction)


@router.patch("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    transaction = transaction_service.get_transaction_for_user(db, transaction_id, current_user.id)
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    updated = transaction_service.update_transaction(db, transaction, payload)
    return TransactionRead.model_validate(updated)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    transaction = transaction_service.get_transaction_for_user(db, transaction_id, current_user.id)
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    transaction_service.delete_transaction(db, transaction)
