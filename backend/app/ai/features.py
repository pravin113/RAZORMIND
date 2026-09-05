from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


FRAUD_FEATURES = [
    "amount",
    "currency",
    "payment_method",
    "transaction_hour",
    "day_of_week",
    "customer_transaction_count",
    "customer_avg_amount",
    "merchant_avg_amount",
    "amount_deviation",
    "customer_age_days",
    "failed_attempts",
    "device_change",
    "ip_change",
    "country_change",
    "velocity_1h",
    "velocity_24h",
    "previous_chargebacks",
    "previous_fraud_events",
    "checkout_duration",
    "retry_count",
    "subscription",
]

RECOVERY_FEATURES = [
    "amount",
    "currency",
    "payment_method",
    "transaction_hour",
    "day_of_week",
    "customer_transaction_count",
    "customer_avg_amount",
    "merchant_avg_amount",
    "amount_deviation",
    "customer_age_days",
    "failed_attempts",
    "checkout_duration",
    "retry_count",
    "subscription",
    "transaction_status",
    "payment_failure",
    "failure_reason",
    "subscription_status",
    "customer_value",
    "previous_successful_payments",
    "recovery_attempts",
]

ANOMALY_FEATURES = [
    "amount",
    "transaction_hour",
    "day_of_week",
    "customer_transaction_count",
    "customer_avg_amount",
    "merchant_avg_amount",
    "amount_deviation",
    "customer_age_days",
    "failed_attempts",
    "device_change",
    "ip_change",
    "country_change",
    "velocity_1h",
    "velocity_24h",
    "previous_chargebacks",
    "previous_fraud_events",
    "checkout_duration",
    "retry_count",
    "subscription",
]

CATEGORICAL_FEATURES = {
    "currency",
    "payment_method",
    "transaction_status",
    "failure_reason",
    "subscription_status",
}


@dataclass(frozen=True)
class FeaturePipeline:
    features: list[str]
    preprocessor: ColumnTransformer


def split_feature_types(features: Iterable[str]) -> tuple[list[str], list[str]]:
    feature_list = list(features)
    categorical = [feature for feature in feature_list if feature in CATEGORICAL_FEATURES]
    numeric = [feature for feature in feature_list if feature not in CATEGORICAL_FEATURES]
    return numeric, categorical


def build_preprocessor(features: Iterable[str], scale_numeric: bool = False) -> ColumnTransformer:
    numeric_features, categorical_features = split_feature_types(features)

    numeric_steps: list[tuple[str, object]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", Pipeline(steps=numeric_steps), numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
    )


def prepare_features(data: pd.DataFrame | dict, features: Iterable[str]) -> pd.DataFrame:
    frame = pd.DataFrame([data]) if isinstance(data, dict) else data.copy()
    for feature in features:
        if feature not in frame.columns:
            frame[feature] = None
    return frame[list(features)]


def save_artifact(artifact: object, path) -> None:
    joblib.dump(artifact, path)


def load_artifact(path):
    return joblib.load(path)

