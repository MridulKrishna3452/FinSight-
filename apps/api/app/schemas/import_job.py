import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import ImportJobStatus


class ImportJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    status: ImportJobStatus
    total_rows: int
    imported_rows: int
    duplicate_rows: int
    failed_rows: int
    suspicious_rows: int
    error_message: str | None
    result_summary: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class ImportPreviewRow(BaseModel):
    row_number: int
    date: str | None
    description: str | None
    amount: str | None
    type: str | None
    merchant: str | None
    payment_method: str | None
    valid: bool
    errors: list[str] = []


class ImportPreviewResponse(BaseModel):
    filename: str
    total_rows: int
    preview_rows: list[ImportPreviewRow]
    detected_columns: dict[str, str]
