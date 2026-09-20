import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CategorizationSource, Category, TransactionType


class TransactionBase(BaseModel):
    transaction_date: date
    merchant_name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    transaction_type: TransactionType
    category: Category | None = None
    payment_method: str = Field(default="Other", max_length=100)
    is_recurring: bool = False


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    transaction_date: date | None = None
    merchant_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    transaction_type: TransactionType | None = None
    category: Category | None = None
    payment_method: str | None = Field(default=None, max_length=100)
    is_recurring: bool | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    transaction_date: date
    merchant_name: str
    description: str
    amount: Decimal
    transaction_type: TransactionType
    category: Category
    categorization_source: CategorizationSource
    payment_method: str
    is_recurring: bool
    anomaly_score: Decimal
    is_suspicious: bool
    anomaly_explanation: str | None
    created_at: datetime


class TransactionFilters(BaseModel):
    search: str | None = None
    category: Category | None = None
    transaction_type: TransactionType | None = None
    is_suspicious: bool | None = None
    date_from: date | None = None
    date_to: date | None = None
    sort_by: str = "transaction_date"
    sort_dir: str = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=200)
