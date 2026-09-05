from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from app.ai.paths import PROCESSED_DATA_DIR, RAW_DATA_DIR, ensure_project_dirs


def _sigmoid(values):
    return 1 / (1 + np.exp(-values))


def generate_synthetic_transactions(record_count: int = 50_000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    merchant_count = 650
    customer_count = 18_000

    merchant_ids = np.array([f"merchant_{idx:05d}" for idx in range(merchant_count)])
    customer_ids = np.array([f"customer_{idx:06d}" for idx in range(customer_count)])
    transaction_ids = np.array([f"txn_{idx:08d}" for idx in range(record_count)])

    merchant_id = rng.choice(merchant_ids, size=record_count)
    customer_id = rng.choice(customer_ids, size=record_count)
    payment_method = rng.choice(
        ["upi", "card", "netbanking", "wallet", "emi"],
        size=record_count,
        p=[0.48, 0.28, 0.12, 0.09, 0.03],
    )
    currency = rng.choice(["INR", "USD"], size=record_count, p=[0.985, 0.015])

    merchant_scale = rng.lognormal(mean=7.1, sigma=0.45, size=merchant_count)
    merchant_lookup = dict(zip(merchant_ids, merchant_scale, strict=True))
    merchant_avg_amount = np.array([merchant_lookup[mid] for mid in merchant_id])
    customer_avg_amount = np.maximum(100, merchant_avg_amount * rng.lognormal(mean=-0.05, sigma=0.55, size=record_count))
    amount = np.maximum(50, customer_avg_amount * rng.lognormal(mean=0.0, sigma=0.75, size=record_count))
    amount = np.round(amount, 2)
    amount_deviation = np.round((amount - customer_avg_amount) / np.maximum(customer_avg_amount, 1), 4)

    hour_probabilities = np.array(
        [0.025, 0.018, 0.014, 0.012, 0.011, 0.015, 0.025, 0.04, 0.05, 0.055, 0.055, 0.06,
         0.065, 0.065, 0.06, 0.055, 0.055, 0.06, 0.065, 0.065, 0.055, 0.045, 0.035, 0.025]
    )
    transaction_hour = rng.choice(np.arange(24), size=record_count, p=hour_probabilities / hour_probabilities.sum())
    day_of_week = rng.integers(0, 7, size=record_count)
    customer_transaction_count = rng.negative_binomial(8, 0.35, size=record_count) + 1
    customer_age_days = rng.integers(0, 2200, size=record_count)
    failed_attempts = rng.poisson(0.35, size=record_count)
    velocity_1h = rng.poisson(0.8, size=record_count)
    velocity_24h = velocity_1h + rng.poisson(3.5, size=record_count)
    previous_chargebacks = rng.poisson(0.06, size=record_count)
    previous_fraud_events = rng.poisson(0.03, size=record_count)
    checkout_duration = np.round(rng.gamma(shape=2.2, scale=28, size=record_count), 2)
    retry_count = rng.poisson(0.4, size=record_count)
    subscription = rng.binomial(1, 0.22, size=record_count)

    risky_context = (
        (amount_deviation > 2.5).astype(int)
        + (transaction_hour <= 4).astype(int)
        + (failed_attempts >= 2).astype(int)
        + (velocity_1h >= 4).astype(int)
        + (velocity_24h >= 12).astype(int)
        + (previous_chargebacks > 0).astype(int)
        + (previous_fraud_events > 0).astype(int)
    )
    device_change_prob = np.clip(0.05 + 0.10 * risky_context, 0, 0.75)
    ip_change_prob = np.clip(0.08 + 0.08 * risky_context, 0, 0.75)
    country_change_prob = np.clip(0.015 + 0.05 * risky_context, 0, 0.55)
    device_change = rng.binomial(1, device_change_prob)
    ip_change = rng.binomial(1, ip_change_prob)
    country_change = rng.binomial(1, country_change_prob)

    fraud_logit = (
        -5.4
        + 0.55 * (amount_deviation > 2.0)
        + 0.65 * (transaction_hour <= 4)
        + 0.75 * (failed_attempts >= 2)
        + 0.6 * device_change
        + 0.65 * ip_change
        + 0.95 * country_change
        + 0.55 * (velocity_1h >= 4)
        + 0.45 * (velocity_24h >= 12)
        + 0.9 * (previous_chargebacks > 0)
        + 1.15 * (previous_fraud_events > 0)
        + 0.25 * (payment_method == "card")
        - 0.35 * subscription
    )
    is_fraud = rng.binomial(1, _sigmoid(fraud_logit))

    payment_failure_prob = np.clip(
        0.08
        + 0.08 * (failed_attempts >= 1)
        + 0.06 * (retry_count >= 2)
        + 0.04 * (checkout_duration > 100)
        + 0.05 * (payment_method == "card")
        - 0.03 * subscription,
        0.02,
        0.65,
    )
    payment_failure = rng.binomial(1, payment_failure_prob)
    transaction_status = np.where(
        payment_failure == 1,
        rng.choice(["failed", "authorized"], size=record_count, p=[0.82, 0.18]),
        rng.choice(["captured", "refunded"], size=record_count, p=[0.97, 0.03]),
    )
    failure_reason = np.where(
        payment_failure == 1,
        rng.choice(
            ["insufficient_funds", "bank_declined", "network_error", "authentication_failed"],
            size=record_count,
            p=[0.36, 0.27, 0.22, 0.15],
        ),
        "none",
    )
    subscription_status = np.where(
        subscription == 1,
        rng.choice(["active", "past_due", "cancelled"], size=record_count, p=[0.78, 0.16, 0.06]),
        "none",
    )
    customer_value = np.round(customer_avg_amount * np.maximum(customer_transaction_count, 1), 2)
    previous_successful_payments = np.maximum(0, customer_transaction_count - failed_attempts - rng.poisson(0.5, record_count))
    recovery_attempts = np.where(payment_failure == 1, rng.poisson(0.9, record_count), 0)
    recovery_logit = (
        -0.7
        + 0.45 * subscription
        + 0.35 * (subscription_status == "active")
        + 0.55 * (previous_successful_payments >= 3)
        + 0.35 * (failure_reason == "network_error")
        - 0.45 * (failure_reason == "bank_declined")
        - 0.35 * (recovery_attempts >= 3)
        - 0.25 * is_fraud
    )
    recovered = np.where(payment_failure == 1, rng.binomial(1, _sigmoid(recovery_logit)), 0)
    recovery_action = np.where(
        payment_failure == 1,
        rng.choice(["retry_link", "upi_reminder", "card_update", "support_outreach"], size=record_count),
        "none",
    )
    recovery_amount = np.where(recovered == 1, np.round(amount * rng.uniform(0.75, 1.0, record_count), 2), 0.0)

    return pd.DataFrame(
        {
            "transaction_id": transaction_ids,
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "transaction_hour": transaction_hour,
            "day_of_week": day_of_week,
            "customer_transaction_count": customer_transaction_count,
            "customer_avg_amount": np.round(customer_avg_amount, 2),
            "merchant_avg_amount": np.round(merchant_avg_amount, 2),
            "amount_deviation": amount_deviation,
            "customer_age_days": customer_age_days,
            "failed_attempts": failed_attempts,
            "device_change": device_change,
            "ip_change": ip_change,
            "country_change": country_change,
            "velocity_1h": velocity_1h,
            "velocity_24h": velocity_24h,
            "previous_chargebacks": previous_chargebacks,
            "previous_fraud_events": previous_fraud_events,
            "checkout_duration": checkout_duration,
            "retry_count": retry_count,
            "subscription": subscription,
            "transaction_status": transaction_status,
            "is_fraud": is_fraud,
            "payment_failure": payment_failure,
            "failure_reason": failure_reason,
            "subscription_status": subscription_status,
            "customer_value": customer_value,
            "previous_successful_payments": previous_successful_payments,
            "recovery_attempts": recovery_attempts,
            "recovered": recovered,
            "recovery_action": recovery_action,
            "recovery_amount": recovery_amount,
        }
    )


def generate_and_save(record_count: int = 50_000, seed: int = 42) -> dict:
    ensure_project_dirs()
    data = generate_synthetic_transactions(record_count=record_count, seed=seed)
    raw_path = RAW_DATA_DIR / "synthetic_transactions.csv"
    processed_path = PROCESSED_DATA_DIR / "transactions.csv"
    metadata_path = PROCESSED_DATA_DIR / "dataset_metadata.json"

    data.to_csv(raw_path, index=False)
    data.to_csv(processed_path, index=False)

    metadata = {
        "record_count": int(len(data)),
        "fraud_count": int(data["is_fraud"].sum()),
        "fraud_rate": float(data["is_fraud"].mean()),
        "payment_failure_rate": float(data["payment_failure"].mean()),
        "recovery_rate_on_failures": float(data.loc[data["payment_failure"] == 1, "recovered"].mean()),
        "seed": seed,
        "raw_path": str(raw_path),
        "processed_path": str(processed_path),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    result = generate_and_save(record_count=args.records, seed=args.seed)
    print(json.dumps(result, indent=2))
