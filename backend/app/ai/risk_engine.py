from __future__ import annotations

from dataclasses import dataclass

from app.ai.anomaly.predict import predict_anomaly
from app.ai.fraud.predict import predict_fraud


@dataclass(frozen=True)
class RiskWeights:
    fraud_probability: float = 0.65
    anomaly_score: float = 0.25
    business_rules: float = 0.10


def business_rule_score(transaction: dict) -> float:
    score = 0.0
    if float(transaction.get("amount_deviation") or 0) > 3:
        score += 0.25
    if int(transaction.get("failed_attempts") or 0) >= 3:
        score += 0.20
    if int(transaction.get("country_change") or 0) == 1:
        score += 0.25
    if int(transaction.get("previous_chargebacks") or 0) > 0:
        score += 0.15
    if int(transaction.get("velocity_1h") or 0) >= 5:
        score += 0.15
    return min(score, 1.0)


def risk_level_for_score(score: float) -> str:
    if score >= 0.85:
        return "CRITICAL"
    if score >= 0.65:
        return "HIGH"
    if score >= 0.35:
        return "MEDIUM"
    return "LOW"


def analyze_risk(transaction: dict, weights: RiskWeights | None = None) -> dict:
    selected_weights = weights or RiskWeights()
    fraud = predict_fraud(transaction)
    anomaly = predict_anomaly(transaction)
    rules = business_rule_score(transaction)
    risk_score = (
        selected_weights.fraud_probability * fraud["fraud_probability"]
        + selected_weights.anomaly_score * anomaly["anomaly_score"]
        + selected_weights.business_rules * rules
    )
    risk_score = max(0.0, min(float(risk_score), 1.0))
    return {
        "fraud_probability": fraud["fraud_probability"],
        "anomaly_score": anomaly["anomaly_score"],
        "anomaly_flag": anomaly["anomaly_flag"],
        "business_rule_score": rules,
        "risk_score": risk_score,
        "risk_level": risk_level_for_score(risk_score),
        "model_version": fraud["model_version"],
    }

