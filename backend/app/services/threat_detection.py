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
_MODEL_SOURCE = None


def _resolve_model_path(raw_model_path: str) -> Path:
    configured_path = Path(raw_model_path)
    if configured_path.is_absolute():
        return configured_path

    app_root = Path(current_app.root_path)
    candidates = [
        app_root / configured_path,
        app_root.parent / configured_path,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def _load_model() -> Optional[object]:
    global _MODEL, _MODEL_SOURCE

    model_path = _resolve_model_path(current_app.config["MODEL_PATH"])
    model_key = str(model_path.resolve()) if model_path.exists() else str(model_path)

    if _MODEL is not None and _MODEL_SOURCE == model_key:
        return _MODEL

    if not model_path.exists():
        return None

    try:
        with model_path.open("rb") as f:
            _MODEL = pickle.load(f)
            _MODEL_SOURCE = model_key
    except Exception:
        current_app.logger.exception("Failed to load threat model from %s", model_path)
        _MODEL = None
        _MODEL_SOURCE = None
        return None

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
