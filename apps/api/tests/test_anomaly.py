from datetime import date

import pytest
from fastapi.testclient import TestClient
from sklearn.ensemble import IsolationForest

from app.ml import model_registry
from app.ml.features import FEATURE_NAMES, UserHistoryStats, build_feature_vector
from app.services import anomaly_service


def test_build_feature_vector_shape() -> None:
    stats = UserHistoryStats()
    features = build_feature_vector(
        amount=500.0,
        category="Dining",
        merchant_name="Swiggy",
        day_of_week=2,
        hour_of_day=12,
        stats=stats,
    )
    assert len(features) == len(FEATURE_NAMES)


def test_feature_vector_zscore_zero_with_no_history() -> None:
    stats = UserHistoryStats()
    features = build_feature_vector(
        amount=500.0,
        category="Dining",
        merchant_name="Swiggy",
        day_of_week=2,
        hour_of_day=12,
        stats=stats,
    )
    category_zscore_idx = FEATURE_NAMES.index("category_amount_zscore")
    assert features[category_zscore_idx] == 0.0


def test_score_transaction_without_model_returns_zero(
    client: TestClient, db_session, test_user, monkeypatch
) -> None:
    monkeypatch.setattr(model_registry, "get_anomaly_model", lambda: None)
    monkeypatch.setattr(anomaly_service, "get_anomaly_model", lambda: None)

    result = anomaly_service.score_transaction(
        db_session, test_user.id, 500.0, "Dining", "Swiggy", date.today()
    )
    assert result.score == 0.0
    assert result.is_suspicious is False
    assert result.explanation is None


@pytest.fixture
def fitted_model(monkeypatch) -> model_registry.AnomalyModel:
    import numpy as np

    normal_data = np.random.RandomState(0).normal(loc=0, scale=1, size=(200, len(FEATURE_NAMES)))
    model = IsolationForest(n_estimators=50, contamination=0.05, random_state=0)
    model.fit(normal_data)
    raw_scores = -model.score_samples(normal_data)

    anomaly_model = model_registry.AnomalyModel(
        model=model,
        feature_names=FEATURE_NAMES,
        score_min=float(raw_scores.min()),
        score_max=float(raw_scores.max()),
        version="test",
    )
    monkeypatch.setattr(anomaly_service, "get_anomaly_model", lambda: anomaly_model)
    return anomaly_model


def test_large_outlier_scores_higher_than_typical_transaction(
    db_session, test_user, fitted_model
) -> None:
    typical = anomaly_service.score_transaction(
        db_session, test_user.id, 500.0, "Dining", "Swiggy", date.today()
    )
    outlier = anomaly_service.score_transaction(
        db_session, test_user.id, 500000.0, "Dining", "Brand New Unusual Merchant", date.today()
    )
    assert outlier.score >= typical.score
