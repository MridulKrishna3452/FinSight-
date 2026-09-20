from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.insight import (
    CategorySpend,
    DailySpendPoint,
    ForecastResponse,
    InsightsDashboardResponse,
    MonthlySummaryItem,
    RecurringExpense,
    TopMerchant,
)
from app.services import forecasting_service, insight_service

router = APIRouter()


@router.get("/dashboard", response_model=InsightsDashboardResponse)
def get_dashboard(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> InsightsDashboardResponse:
    today = date.today()
    summary = insight_service.dashboard_summary(db, current_user.id, today)
    category_spend = insight_service.spending_by_category(
        db, current_user.id, today.year, today.month
    )
    cards = insight_service.generate_insight_cards(db, current_user.id, today)

    return InsightsDashboardResponse(
        summary=summary,
        spending_by_category=category_spend,
        recent_transactions_count=summary.transaction_count,
        insight_cards=cards,
    )


@router.get("/spending-by-category", response_model=list[CategorySpend])
def get_spending_by_category(
    year: int | None = None,
    month: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CategorySpend]:
    return insight_service.spending_by_category(db, current_user.id, year, month)


@router.get("/monthly-summary", response_model=list[MonthlySummaryItem])
def get_monthly_summary(
    months: int = 6,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MonthlySummaryItem]:
    return insight_service.monthly_summary(db, current_user.id, months)


@router.get("/daily-spending", response_model=list[DailySpendPoint])
def get_daily_spending(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DailySpendPoint]:
    return insight_service.daily_spending_trend(db, current_user.id, days)


@router.get("/top-merchants", response_model=list[TopMerchant])
def get_top_merchants(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TopMerchant]:
    return insight_service.top_merchants(db, current_user.id, limit)


@router.get("/forecast", response_model=ForecastResponse)
def get_forecast(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ForecastResponse:
    return forecasting_service.forecast_expenses(db, current_user.id)


@router.get("/recurring-expenses", response_model=list[RecurringExpense])
def get_recurring_expenses(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[RecurringExpense]:
    return insight_service.recurring_expenses(db, current_user.id)
