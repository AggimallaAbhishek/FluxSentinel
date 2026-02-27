import pickle
from pathlib import Path


FEATURE_ORDER = [
    "request_rate",
    "failed_login_ratio",
    "unique_endpoints_count",
    "time_gap_between_requests",
    "payload_size_anomaly",
]


def load_model(model_path: Path = Path(__file__).with_name("model.pkl")):
    with model_path.open("rb") as f:
        return pickle.load(f)


def predict(features: dict, model_path: Path = Path(__file__).with_name("model.pkl")):
    model = load_model(model_path)
    vector = [[features[key] for key in FEATURE_ORDER]]

    probability = float(model.predict_proba(vector)[0][1])
    prediction = 1 if probability >= 0.5 else 0
    severity = int(round(probability * 100))

    return prediction, probability, severity
