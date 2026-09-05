from __future__ import annotations

from app.ai.features import prepare_features
from app.ai.model_io import load_model_bundle


def predict_fraud(transaction: dict) -> dict:
    bundle = load_model_bundle("fraud_model.joblib")
    features = prepare_features(transaction, bundle["features"])
    probability = float(bundle["model"].predict_proba(features)[0][1])
    return {
        "fraud_probability": probability,
        "model_version": bundle["version"],
        "model_name": bundle["model_name"],
    }

