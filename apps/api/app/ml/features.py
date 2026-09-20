"""Shared feature engineering for anomaly detection, used identically at
training time (train_anomaly_model.py, over synthetic data) and at inference
time (anomaly_service.py, over live per-user history) so the model sees the
same feature distribution in both places.
"""

import math
from dataclasses import dataclass, field

FEATURE_NAMES = [
    "log_amount",
    "hour_of_day",
    "day_of_week",
    "category_frequency",
    "merchant_frequency",
    "category_amount_zscore",
    "overall_amount_zscore",
]


@dataclass
class UserHistoryStats:
    """Aggregate stats about a user's transaction history, used to derive
    deviation and frequency features for a new/candidate transaction."""

    total_transaction_count: int = 0
    category_counts: dict[str, int] = field(default_factory=dict)
    merchant_counts: dict[str, int] = field(default_factory=dict)
    category_mean: dict[str, float] = field(default_factory=dict)
    category_std: dict[str, float] = field(default_factory=dict)
    overall_mean: float = 0.0
    overall_std: float = 0.0


def build_feature_vector(
    amount: float,
    category: str,
    merchant_name: str,
    day_of_week: int,
    hour_of_day: int,
    stats: UserHistoryStats,
) -> list[float]:
    log_amount = math.log1p(max(amount, 0.0))

    total = max(stats.total_transaction_count, 1)
    category_frequency = stats.category_counts.get(category, 0) / total
    merchant_frequency = stats.merchant_counts.get(merchant_name, 0) / total

    cat_mean = stats.category_mean.get(category)
    cat_std = stats.category_std.get(category)
    if cat_mean is not None and cat_std and cat_std > 1e-6:
        category_amount_zscore = (amount - cat_mean) / cat_std
    else:
        category_amount_zscore = 0.0

    if stats.overall_std and stats.overall_std > 1e-6:
        overall_amount_zscore = (amount - stats.overall_mean) / stats.overall_std
    else:
        overall_amount_zscore = 0.0

    # Clip extreme z-scores so a single wild outlier doesn't dominate the vector.
    category_amount_zscore = max(min(category_amount_zscore, 10.0), -10.0)
    overall_amount_zscore = max(min(overall_amount_zscore, 10.0), -10.0)

    return [
        log_amount,
        float(hour_of_day),
        float(day_of_week),
        category_frequency,
        merchant_frequency,
        category_amount_zscore,
        overall_amount_zscore,
    ]
