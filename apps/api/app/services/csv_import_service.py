"""CSV import parsing, validation, preview, and processing.

Column header mapping is lenient: several common alternative header spellings
are accepted and normalized to the canonical set (date, description, amount,
type, merchant, payment_method). Actual DB writes happen in `process_import`,
which is invoked from the Celery task (app/workers/tasks.py) so large files
don't block the request/response cycle.
"""

import io
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import TransactionType
from app.models.import_job import ImportJob
from app.models.transaction import Transaction
from app.schemas.import_job import ImportPreviewRow
from app.services import anomaly_service, categorization_service, transaction_service

COLUMN_ALIASES: dict[str, list[str]] = {
    "date": ["date", "transaction_date", "txn_date", "value_date"],
    "description": ["description", "narration", "details", "particulars", "remarks"],
    "amount": ["amount", "value", "txn_amount", "amt"],
    "type": ["type", "transaction_type", "txn_type", "dr_cr"],
    "merchant": ["merchant", "merchant_name", "payee", "vendor"],
    "payment_method": ["payment_method", "mode", "channel", "payment_mode"],
}

REQUIRED_COLUMNS = ["date", "description", "amount"]
MAX_PREVIEW_ROWS = 10


class CSVValidationError(Exception):
    pass


def detect_columns(raw_columns: list[str]) -> dict[str, str]:
    normalized = {col: col.strip().lower().replace(" ", "_") for col in raw_columns}
    detected: dict[str, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for raw_col, norm_col in normalized.items():
            if norm_col in aliases:
                detected[canonical] = raw_col
                break
    return detected


def read_csv(content: bytes) -> pd.DataFrame:
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise CSVValidationError(f"Could not parse CSV file: {exc}") from exc
    if df.empty:
        raise CSVValidationError("CSV file has no data rows.")
    return df


def _normalize_row(row: pd.Series, column_map: dict[str, str]) -> dict[str, str | None]:
    def get(field: str) -> str | None:
        col = column_map.get(field)
        if col is None or col not in row:
            return None
        value = row[col]
        if pd.isna(value):
            return None
        return str(value).strip()

    return {
        "date": get("date"),
        "description": get("description"),
        "amount": get("amount"),
        "type": get("type"),
        "merchant": get("merchant"),
        "payment_method": get("payment_method"),
    }


def _validate_normalized_row(normalized: dict[str, str | None]) -> list[str]:
    errors: list[str] = []
    if not normalized["date"]:
        errors.append("Missing date")
    else:
        try:
            pd.to_datetime(normalized["date"])
        except Exception:
            errors.append("Invalid date format")

    if not normalized["description"]:
        errors.append("Missing description")

    if not normalized["amount"]:
        errors.append("Missing amount")
    else:
        try:
            Decimal(str(normalized["amount"]).replace(",", ""))
        except InvalidOperation:
            errors.append("Invalid amount")

    return errors


def build_preview(content: bytes) -> tuple[list[ImportPreviewRow], dict[str, str], int]:
    df = read_csv(content)
    column_map = detect_columns(list(df.columns))

    missing_required = [c for c in REQUIRED_COLUMNS if c not in column_map]
    if missing_required:
        raise CSVValidationError(
            f"CSV is missing required column(s): {', '.join(missing_required)}. "
            f"Detected columns: {list(df.columns)}"
        )

    preview_rows: list[ImportPreviewRow] = []
    for idx, row in df.head(MAX_PREVIEW_ROWS).iterrows():
        normalized = _normalize_row(row, column_map)
        errors = _validate_normalized_row(normalized)
        preview_rows.append(
            ImportPreviewRow(
                row_number=int(idx) + 1,
                date=normalized["date"],
                description=normalized["description"],
                amount=normalized["amount"],
                type=normalized["type"],
                merchant=normalized["merchant"],
                payment_method=normalized["payment_method"],
                valid=len(errors) == 0,
                errors=errors,
            )
        )

    return preview_rows, column_map, len(df)


def _infer_type_and_amount(
    amount_str: str, type_str: str | None
) -> tuple[TransactionType, Decimal]:
    amount = Decimal(str(amount_str).replace(",", ""))
    if type_str:
        normalized_type = type_str.strip().lower()
        if normalized_type in ("income", "credit", "cr"):
            return TransactionType.INCOME, abs(amount)
        if normalized_type in ("expense", "debit", "dr"):
            return TransactionType.EXPENSE, abs(amount)
    # Fall back to sign of amount: negative = expense, positive = income.
    if amount < 0:
        return TransactionType.EXPENSE, abs(amount)
    return TransactionType.INCOME, amount


def process_import(db: Session, job: ImportJob, content: bytes) -> None:
    df = read_csv(content)
    column_map = detect_columns(list(df.columns))
    job.total_rows = len(df)

    imported = 0
    duplicates = 0
    failed = 0
    suspicious = 0

    existing_hashes = set(
        db.execute(select(Transaction.dedup_hash).where(Transaction.user_id == job.user_id))
        .scalars()
        .all()
    )

    for _, row in df.iterrows():
        normalized = _normalize_row(row, column_map)
        errors = _validate_normalized_row(normalized)
        if errors:
            failed += 1
            continue

        amount_str = normalized["amount"]
        if amount_str is None:
            failed += 1
            continue

        try:
            transaction_date = pd.to_datetime(normalized["date"]).date()
            transaction_type, amount = _infer_type_and_amount(amount_str, normalized["type"])
        except Exception:
            failed += 1
            continue

        description = normalized["description"] or ""
        merchant_name = normalized["merchant"] or description[:255]
        payment_method = normalized["payment_method"] or "Other"

        dedup_hash = transaction_service.compute_dedup_hash(
            job.user_id, transaction_date, amount, description
        )
        if dedup_hash in existing_hashes:
            duplicates += 1
            continue
        existing_hashes.add(dedup_hash)

        categorization = categorization_service.categorize(merchant_name, description)

        transaction = Transaction(
            user_id=job.user_id,
            transaction_date=transaction_date,
            merchant_name=merchant_name,
            description=description,
            amount=amount,
            transaction_type=transaction_type,
            category=categorization.category,
            categorization_source=categorization.source,
            payment_method=payment_method,
            dedup_hash=dedup_hash,
            import_job_id=job.id,
        )

        if transaction_type == TransactionType.EXPENSE:
            anomaly = anomaly_service.score_transaction(
                db,
                job.user_id,
                float(amount),
                categorization.category.value,
                merchant_name,
                transaction_date,
            )
            transaction.anomaly_score = Decimal(str(anomaly.score))
            transaction.is_suspicious = anomaly.is_suspicious
            transaction.anomaly_explanation = anomaly.explanation
            if anomaly.is_suspicious:
                suspicious += 1

        db.add(transaction)
        imported += 1

    job.imported_rows = imported
    job.duplicate_rows = duplicates
    job.failed_rows = failed
    job.suspicious_rows = suspicious
    job.result_summary = {
        "imported": imported,
        "duplicates": duplicates,
        "failed": failed,
        "suspicious": suspicious,
        "total": len(df),
        "processed_at": datetime.now(UTC).isoformat(),
    }
    db.commit()

    _create_post_import_alerts(db, job)


def _create_post_import_alerts(db: Session, job: ImportJob) -> None:
    from app.models.budget import Budget
    from app.services import alert_service, budget_service

    new_transactions = list(
        db.execute(select(Transaction).where(Transaction.import_job_id == job.id)).scalars().all()
    )

    for transaction in new_transactions:
        if transaction.is_suspicious:
            alert_service.create_suspicious_transaction_alert(db, transaction)

    touched_periods = {
        (t.transaction_date.year, t.transaction_date.month) for t in new_transactions
    }
    if not touched_periods:
        return

    budgets = list(db.execute(select(Budget).where(Budget.user_id == job.user_id)).scalars().all())
    for budget in budgets:
        if (budget.year, budget.month) in touched_periods:
            budget_service.check_and_create_threshold_alerts(db, job.user_id, budget)
