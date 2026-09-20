from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    balance: Decimal
    monthly_income: Decimal
    monthly_expense: Decimal
    savings_rate: float
    transaction_count: int


class CategorySpend(BaseModel):
    category: str
    total: Decimal
    percent: float
    transaction_count: int


class MonthlySummaryItem(BaseModel):
    month: str
    income: Decimal
    expense: Decimal


class DailySpendPoint(BaseModel):
    date: date
    amount: Decimal


class TopMerchant(BaseModel):
    merchant_name: str
    total: Decimal
    transaction_count: int
    category: str


class RecurringExpense(BaseModel):
    merchant_name: str
    category: str
    average_amount: Decimal
    occurrences: int
    last_date: date


class ForecastPoint(BaseModel):
    date: date
    predicted_amount: Decimal


class ForecastResponse(BaseModel):
    method: str
    disclaimer: str
    historical_daily_average: Decimal
    points: list[ForecastPoint]


class InsightCard(BaseModel):
    id: str
    severity: str
    title: str
    message: str


class InsightsDashboardResponse(BaseModel):
    summary: DashboardSummary
    spending_by_category: list[CategorySpend]
    recent_transactions_count: int
    insight_cards: list[InsightCard]
