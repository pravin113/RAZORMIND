from decimal import Decimal

import pandas as pd

from app.ai.anomaly.predict import predict_anomaly
from app.ai.dataset import generate_synthetic_transactions
from app.ai.features import FRAUD_FEATURES, build_preprocessor, prepare_features
from app.ai.fraud.predict import predict_fraud
from app.ai.recovery.predict import predict_recovery
from app.ai.risk_engine import analyze_risk, business_rule_score, risk_level_for_score


SAMPLE_TRANSACTION = {
    "amount": 2499.0,
    "currency": "INR",
    "payment_method": "upi",
    "transaction_hour": 23,
    "day_of_week": 4,
    "customer_transaction_count": 8,
    "customer_avg_amount": 1800.0,
    "merchant_avg_amount": 2100.0,
    "amount_deviation": 0.39,
    "customer_age_days": 240,
    "failed_attempts": 1,
    "device_change": 0,
    "ip_change": 1,
    "country_change": 0,
    "velocity_1h": 2,
    "velocity_24h": 6,
    "previous_chargebacks": 0,
    "previous_fraud_events": 0,
    "checkout_duration": 48.5,
    "retry_count": 1,
    "subscription": 1,
    "transaction_status": "failed",
    "payment_failure": 1,
    "failure_reason": "network_error",
    "subscription_status": "active",
    "customer_value": 14500.0,
    "previous_successful_payments": 7,
    "recovery_attempts": 1,
}


def test_dataset_generation_has_expected_shape_and_imbalance():
    data = generate_synthetic_transactions(record_count=1000, seed=7)

    assert len(data) == 1000
    assert {"transaction_id", "merchant_id", "is_fraud", "recovered"}.issubset(data.columns)
    assert 0 < data["is_fraud"].mean() < 0.08
    assert data["payment_failure"].isin([0, 1]).all()


def test_feature_engineering_handles_missing_and_categorical_values():
    data = pd.DataFrame(
        [
            {"amount": 1000, "currency": "INR", "payment_method": "upi"},
            {"amount": None, "currency": "INR", "payment_method": "card"},
        ]
    )
    prepared = prepare_features(data, FRAUD_FEATURES)
    transformed = build_preprocessor(FRAUD_FEATURES).fit_transform(prepared)

    assert transformed.shape[0] == 2
    assert len(prepared.columns) == len(FRAUD_FEATURES)


def test_fraud_prediction_returns_probability_from_artifact():
    result = predict_fraud(SAMPLE_TRANSACTION)

    assert 0 <= result["fraud_probability"] <= 1
    assert result["model_version"].startswith("fraud-")


def test_anomaly_prediction_returns_score_and_flag_from_artifact():
    result = predict_anomaly(SAMPLE_TRANSACTION)

    assert 0 <= result["anomaly_score"] <= 1
    assert isinstance(result["anomaly_flag"], bool)


def test_recovery_prediction_returns_expected_value_from_artifact():
    result = predict_recovery(SAMPLE_TRANSACTION)

    assert 0 <= result["recovery_probability"] <= 1
    assert result["expected_recovered_value"] >= Decimal("0")
    assert result["recommended_priority"] in {"low", "medium", "high"}


def test_risk_scoring_combines_model_and_business_rule_outputs():
    assert business_rule_score({**SAMPLE_TRANSACTION, "amount_deviation": 4, "failed_attempts": 4}) > 0
    assert risk_level_for_score(0.9) == "CRITICAL"

    result = analyze_risk(SAMPLE_TRANSACTION)

    assert 0 <= result["risk_score"] <= 1
    assert result["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

