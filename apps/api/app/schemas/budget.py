import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Category


class BudgetBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: Category | None = None
    monthly_limit: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    monthly_limit: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: Category | None
    monthly_limit: Decimal
    month: int
    year: int


class BudgetProgress(BudgetRead):
    spent: Decimal
    remaining: Decimal
    percent_consumed: float
    status: str
