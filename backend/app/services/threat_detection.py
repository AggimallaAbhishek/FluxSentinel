import pickle
from pathlib import Path
from typing import Optional

from flask import current_app


FEATURE_ORDER = [
    "request_rate",
    "failed_login_ratio",
    "unique_endpoints_count",
    "time_gap_between_requests",
    "payload_size_anomaly",
]
_MODEL = None


def _load_model() -> Optional[object]:
    global _MODEL

    if _MODEL is not None:
        return _MODEL

    model_path = Path(current_app.config["MODEL_PATH"])
    if not model_path.is_absolute():
        model_path = Path(current_app.root_path) / model_path

    if not model_path.exists():
        return None

    with model_path.open("rb") as f:
        _MODEL = pickle.load(f)
    return _MODEL


def _heuristic_probability(features: dict) -> float:
    score = 0.0
    score += min(features["request_rate"] / 200.0, 0.5)
    score += min(features["failed_login_ratio"], 0.2)
    score += min(features["unique_endpoints_count"] / 50.0, 0.1)
    score += min(features["payload_size_anomaly"] / 10.0, 0.1)
    score += 0.1 if features["time_gap_between_requests"] < 0.05 else 0.0
    return max(0.0, min(score, 1.0))


def predict_threat(features: dict) -> tuple[int, float, int]:
    vector = [[features[key] for key in FEATURE_ORDER]]
    model = _load_model()

    if model is not None and hasattr(model, "predict_proba"):
        probability = float(model.predict_proba(vector)[0][1])
    else:
        probability = _heuristic_probability(features)

    prediction = 1 if probability >= 0.5 else 0
    severity = int(round(probability * 100))
    return prediction, probability, severity
