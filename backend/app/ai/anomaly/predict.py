from __future__ import annotations

import math

from app.ai.features import prepare_features
from app.ai.model_io import load_model_bundle


def predict_anomaly(transaction: dict) -> dict:
    bundle = load_model_bundle("anomaly_model.joblib")
    features = prepare_features(transaction, bundle["features"])
    raw_score = float(-bundle["model"].decision_function(features)[0])
    anomaly_score = 1 / (1 + math.exp(-8 * raw_score))
    return {
        "anomaly_score": anomaly_score,
        "anomaly_flag": raw_score >= bundle["threshold"],
        "model_version": bundle["version"],
    }

