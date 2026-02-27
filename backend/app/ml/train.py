import pickle
from pathlib import Path

import numpy as np
from xgboost import XGBClassifier


def build_synthetic_dataset(samples: int = 2000):
    rng = np.random.default_rng(42)

    request_rate = rng.integers(1, 400, size=samples)
    failed_ratio = rng.uniform(0.0, 1.0, size=samples)
    unique_endpoints = rng.integers(1, 80, size=samples)
    time_gap = rng.uniform(0.001, 2.0, size=samples)
    payload_anomaly = rng.uniform(0.1, 20.0, size=samples)

    X = np.column_stack(
        [request_rate, failed_ratio, unique_endpoints, time_gap, payload_anomaly]
    )

    y = (
        (request_rate > 220)
        | (failed_ratio > 0.6)
        | ((payload_anomaly > 8.0) & (time_gap < 0.05))
    ).astype(int)

    return X, y


def train_model(output_path: Path):
    X, y = build_synthetic_dataset()

    model = XGBClassifier(
        n_estimators=120,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
    )
    model.fit(X, y)

    with output_path.open("wb") as f:
        pickle.dump(model, f)

    print(f"Model saved to {output_path}")


if __name__ == "__main__":
    train_model(Path(__file__).with_name("model.pkl"))
