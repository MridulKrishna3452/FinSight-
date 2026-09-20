"""30-day expense forecast using simple linear regression over daily
aggregated historical expense totals. This is a documented estimate based on
historical imported data, not a guarantee -- see ForecastResponse.disclaimer.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.insight import ForecastPoint, ForecastResponse

FORECAST_HORIZON_DAYS = 30
DISCLAIMER = (
    "This is an estimate based on your historical imported transaction data using a simple "
    "linear trend model. It is not financial advice and actual spending may vary significantly."
)


def forecast_expenses(db: Session, user_id: uuid.UUID) -> ForecastResponse:
    rows = db.execute(
        select(Transaction.transaction_date, func.sum(Transaction.amount))
        .where(
            Transaction.user_id == user_id, Transaction.transaction_type == TransactionType.EXPENSE
        )
        .group_by(Transaction.transaction_date)
        .order_by(Transaction.transaction_date)
    ).all()

    if not rows:
        return ForecastResponse(
            method="linear_regression",
            disclaimer=DISCLAIMER,
            historical_daily_average=Decimal("0"),
            points=[],
        )

    first_date = rows[0][0]
    last_date = rows[-1][0]
    daily_totals: dict[date, float] = {d: float(total) for d, total in rows}

    all_days = [first_date + timedelta(days=i) for i in range((last_date - first_date).days + 1)]
    y = np.array([daily_totals.get(d, 0.0) for d in all_days])
    x = np.arange(len(all_days))

    historical_avg = float(y.mean()) if len(y) else 0.0

    if len(x) < 2 or np.all(y == y[0]):
        slope, intercept = 0.0, historical_avg
    else:
        slope, intercept = np.polyfit(x, y, 1)

    points: list[ForecastPoint] = []
    for i in range(1, FORECAST_HORIZON_DAYS + 1):
        future_x = len(all_days) - 1 + i
        predicted = max(intercept + slope * future_x, 0.0)
        points.append(
            ForecastPoint(
                date=last_date + timedelta(days=i),
                predicted_amount=Decimal(str(round(predicted, 2))),
            )
        )

    return ForecastResponse(
        method="linear_regression",
        disclaimer=DISCLAIMER,
        historical_daily_average=Decimal(str(round(historical_avg, 2))),
        points=points,
    )
