from __future__ import annotations

from decimal import Decimal

from app.ai.features import prepare_features
from app.ai.model_io import load_model_bundle


def predict_recovery(transaction: dict) -> dict:
    bundle = load_model_bundle("recovery_model.joblib")
    features = prepare_features(transaction, bundle["features"])
    probability = float(bundle["model"].predict_proba(features)[0][1])
    amount = Decimal(str(transaction.get("amount", 0)))
    expected_value = amount * Decimal(str(probability))
    if probability >= 0.70:
        priority = "high"
    elif probability >= 0.40:
        priority = "medium"
    else:
        priority = "low"
    return {
        "recovery_probability": probability,
        "expected_recovered_value": expected_value,
        "recommended_priority": priority,
        "model_version": bundle["version"],
        "model_name": bundle["model_name"],
    }

