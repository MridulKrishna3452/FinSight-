"""Anomaly / fraud-risk scoring service.

Scores a candidate transaction against the user's own transaction history
using the pre-trained global Isolation Forest model (app/ml). Produces a
normalized 0-1 anomaly_score and a plain-language, rule-based explanation
derived from the same statistics used to build the feature vector (Isolation
Forest itself gives no per-feature attribution, so explanations are computed
independently from the underlying deviations).

`is_suspicious` is set only when anomaly_score exceeds settings.ANOMALY_THRESHOLD
(documented default: 0.7). Results are risk indicators, not confirmed fraud.
"""

import statistics
import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ml.features import UserHistoryStats, build_feature_vector
from app.ml.model_registry import get_anomaly_model
from app.models.transaction import Transaction


@dataclass
class AnomalyResult:
    score: float
    is_suspicious: bool
    explanation: str | None


def _build_user_history_stats(
    db: Session, user_id: uuid.UUID
) -> tuple[UserHistoryStats, dict[str, list[float]]]:
    rows = db.execute(
        select(Transaction.category, Transaction.merchant_name, Transaction.amount).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
        )
    ).all()

    stats = UserHistoryStats()
    stats.total_transaction_count = len(rows)

    category_amounts: dict[str, list[float]] = {}
    all_amounts: list[float] = []

    for category, merchant_name, amount in rows:
        amount_f = float(amount)
        category_key = category.value if hasattr(category, "value") else category
        stats.category_counts[category_key] = stats.category_counts.get(category_key, 0) + 1
        stats.merchant_counts[merchant_name] = stats.merchant_counts.get(merchant_name, 0) + 1
        category_amounts.setdefault(category_key, []).append(amount_f)
        all_amounts.append(amount_f)

    for category_key, amounts in category_amounts.items():
        stats.category_mean[category_key] = statistics.mean(amounts)
        stats.category_std[category_key] = statistics.stdev(amounts) if len(amounts) > 1 else 0.0

    if all_amounts:
        stats.overall_mean = statistics.mean(all_amounts)
        stats.overall_std = statistics.stdev(all_amounts) if len(all_amounts) > 1 else 0.0

    return stats, category_amounts


def _build_explanation(
    amount: float,
    category: str,
    merchant_name: str,
    stats: UserHistoryStats,
    is_new_merchant: bool,
) -> str | None:
    reasons: list[str] = []

    cat_mean = stats.category_mean.get(category)
    if cat_mean and cat_mean > 0 and amount > cat_mean * 2:
        multiplier = amount / cat_mean
        reasons.append(
            f"This amount is {multiplier:.1f}x higher than your usual {category} expenses."
        )

    if is_new_merchant and stats.overall_mean and amount > stats.overall_mean * 1.5:
        reasons.append("This merchant is new and the transaction is unusually large.")
    elif is_new_merchant and stats.total_transaction_count > 10:
        reasons.append("This is the first transaction with this merchant.")

    if stats.overall_mean and stats.overall_std and stats.overall_std > 0:
        z = (amount - stats.overall_mean) / stats.overall_std
        if z > 3 and not reasons:
            reasons.append("This transaction amount is far outside your typical spending range.")

    if not reasons:
        return None
    return " ".join(reasons)


def score_transaction(
    db: Session,
    user_id: uuid.UUID,
    amount: float,
    category: str,
    merchant_name: str,
    transaction_date: date,
) -> AnomalyResult:
    model = get_anomaly_model()
    stats, _ = _build_user_history_stats(db, user_id)
    is_new_merchant = stats.merchant_counts.get(merchant_name, 0) == 0

    if model is None:
        # Model not trained yet (e.g. fresh dev environment before running the
        # training script). Fail safe: no score, never flagged suspicious.
        return AnomalyResult(score=0.0, is_suspicious=False, explanation=None)

    features = build_feature_vector(
        amount=amount,
        category=category,
        merchant_name=merchant_name,
        day_of_week=transaction_date.weekday(),
        hour_of_day=12,
        stats=stats,
    )
    score = model.normalized_score(features)
    is_suspicious = score >= settings.ANOMALY_THRESHOLD

    explanation = None
    if is_suspicious:
        explanation = _build_explanation(amount, category, merchant_name, stats, is_new_merchant)
        if explanation is None:
            explanation = "This transaction pattern deviates notably from your typical spending."

    return AnomalyResult(
        score=round(score, 3), is_suspicious=is_suspicious, explanation=explanation
    )
