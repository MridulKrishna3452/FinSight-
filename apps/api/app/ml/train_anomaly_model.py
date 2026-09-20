#!/usr/bin/env python3
"""Trains the baseline Isolation Forest anomaly-detection model on synthetic
transaction data and saves it (plus normalization params) via joblib.

This is a reproducible, offline training script -- run it whenever the feature
set changes. It does NOT depend on the database; it fabricates a synthetic
population of users/transactions with realistic spending patterns and a small
fraction of intentionally injected outliers, mirroring how a real user's
transaction history would look, so the Isolation Forest learns a sensible
notion of "normal" for the feature space defined in app/ml/features.py.

Usage:
    python -m app.ml.train_anomaly_model
"""

import random
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.ml.features import FEATURE_NAMES, UserHistoryStats, build_feature_vector  # noqa: E402

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
ARTIFACT_PATH = ARTIFACT_DIR / "anomaly_model.joblib"

CATEGORIES = [
    "Housing",
    "Groceries",
    "Dining",
    "Transport",
    "Shopping",
    "Entertainment",
    "Healthcare",
    "Education",
    "Utilities",
    "Travel",
    "Insurance",
    "Salary",
    "Investments",
    "Transfers",
    "Other",
]
CATEGORY_TYPICAL_RANGE = {
    "Housing": (12000, 25000),
    "Groceries": (300, 3000),
    "Dining": (150, 900),
    "Transport": (80, 600),
    "Shopping": (300, 4000),
    "Entertainment": (150, 800),
    "Healthcare": (150, 2500),
    "Education": (500, 5000),
    "Utilities": (400, 2000),
    "Travel": (1500, 15000),
    "Insurance": (1000, 8000),
    "Salary": (40000, 120000),
    "Investments": (1000, 20000),
    "Transfers": (200, 5000),
    "Other": (100, 2000),
}


def _simulate_user_transactions(rng: random.Random, n_transactions: int) -> list[dict]:
    """Simulate one synthetic user's transaction history with realistic
    per-category spending habits, then return feature rows + outlier labels
    (label used only for reporting/threshold sanity-check, not for fitting)."""
    merchants_per_category = {
        cat: [f"{cat}_merchant_{i}" for i in range(rng.randint(2, 6))] for cat in CATEGORIES
    }
    category_weights = [rng.uniform(0.5, 3.0) for _ in CATEGORIES]
    total_weight = sum(category_weights)
    category_probs = [w / total_weight for w in category_weights]

    history: list[dict] = []
    stats = UserHistoryStats()
    outlier_indices = set(rng.sample(range(n_transactions), k=max(1, int(n_transactions * 0.03))))

    for i in range(n_transactions):
        category = rng.choices(CATEGORIES, weights=category_probs, k=1)[0]
        merchant = rng.choice(merchants_per_category[category])
        low, high = CATEGORY_TYPICAL_RANGE[category]
        amount = rng.uniform(low, high)
        is_injected_outlier = i in outlier_indices
        if is_injected_outlier:
            amount *= rng.uniform(5, 15)
            merchant = f"new_unusual_merchant_{i}"

        day_of_week = rng.randint(0, 6)
        hour_of_day = rng.randint(0, 23)

        features = build_feature_vector(
            amount=amount,
            category=category,
            merchant_name=merchant,
            day_of_week=day_of_week,
            hour_of_day=hour_of_day,
            stats=stats,
        )
        history.append({"features": features, "is_injected_outlier": is_injected_outlier})

        # Update running stats for next iteration (mirrors inference-time behavior).
        stats.total_transaction_count += 1
        stats.category_counts[category] = stats.category_counts.get(category, 0) + 1
        stats.merchant_counts[merchant] = stats.merchant_counts.get(merchant, 0) + 1

        prev_mean = stats.category_mean.get(category, amount)
        prev_std = stats.category_std.get(category, 0.0)
        count = stats.category_counts[category]
        new_mean = prev_mean + (amount - prev_mean) / count
        new_std = (
            np.sqrt(
                ((prev_std**2) * (count - 1) + (amount - prev_mean) * (amount - new_mean)) / count
            )
            if count > 1
            else 0.0
        )
        stats.category_mean[category] = new_mean
        stats.category_std[category] = float(new_std)

        prev_overall_mean = stats.overall_mean
        n = stats.total_transaction_count
        stats.overall_mean = prev_overall_mean + (amount - prev_overall_mean) / n
        stats.overall_std = (
            float(
                np.sqrt(
                    (
                        (stats.overall_std**2) * (n - 1)
                        + (amount - prev_overall_mean) * (amount - stats.overall_mean)
                    )
                    / n
                )
            )
            if n > 1
            else 0.0
        )

    return history


def train(n_users: int = 150, transactions_per_user: int = 120, seed: int = 42) -> None:
    rng = random.Random(seed)
    all_rows: list[dict] = []
    for _ in range(n_users):
        all_rows.extend(_simulate_user_transactions(rng, transactions_per_user))

    X = np.array([row["features"] for row in all_rows])
    labels = np.array([row["is_injected_outlier"] for row in all_rows])

    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X)

    # score_samples: higher = more normal. Flip sign so higher = more anomalous,
    # then min-max normalize to [0, 1] for a human-readable "risk score".
    raw_scores = -model.score_samples(X)
    score_min, score_max = float(raw_scores.min()), float(raw_scores.max())

    normalized = (raw_scores - score_min) / max(score_max - score_min, 1e-9)
    injected_mean = normalized[labels].mean() if labels.any() else None
    normal_mean = normalized[~labels].mean()
    print(f"Trained on {len(all_rows)} synthetic transactions across {n_users} users.")
    print(
        f"Mean normalized anomaly score - injected outliers: {injected_mean:.3f}, "
        f"normal: {normal_mean:.3f}"
    )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "feature_names": FEATURE_NAMES,
            "score_min": score_min,
            "score_max": score_max,
            "version": "1.0.0",
        },
        ARTIFACT_PATH,
    )
    print(f"Saved model to {ARTIFACT_PATH}")


if __name__ == "__main__":
    train()
