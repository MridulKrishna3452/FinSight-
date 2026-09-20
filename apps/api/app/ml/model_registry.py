"""Loads and caches the trained Isolation Forest anomaly model artifact."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np

ARTIFACT_PATH = Path(__file__).resolve().parent / "artifacts" / "anomaly_model.joblib"


@dataclass
class AnomalyModel:
    model: Any
    feature_names: list[str]
    score_min: float
    score_max: float
    version: str

    def normalized_score(self, feature_vector: list[float]) -> float:
        raw = -self.model.score_samples(np.array([feature_vector]))[0]
        score = (raw - self.score_min) / max(self.score_max - self.score_min, 1e-9)
        return float(min(max(score, 0.0), 1.0))


_cached_model: AnomalyModel | None = None


def is_model_available() -> bool:
    return ARTIFACT_PATH.exists()


def get_anomaly_model() -> AnomalyModel | None:
    global _cached_model
    if _cached_model is not None:
        return _cached_model
    if not ARTIFACT_PATH.exists():
        return None
    payload = joblib.load(ARTIFACT_PATH)
    _cached_model = AnomalyModel(
        model=payload["model"],
        feature_names=payload["feature_names"],
        score_min=payload["score_min"],
        score_max=payload["score_max"],
        version=payload["version"],
    )
    return _cached_model
