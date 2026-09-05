from decimal import Decimal


def create_merchant_and_transaction(client):
    merchant_response = client.post(
        "/api/v1/merchants",
        json={
            "name": "ML Merchant",
            "email": "ml@example.test",
            "business_type": "saas",
            "currency": "INR",
        },
    )
    assert merchant_response.status_code == 201
    merchant_id = merchant_response.json()["id"]
    transaction_response = client.post(
        "/api/v1/transactions",
        json={
            "merchant_id": merchant_id,
            "amount": "2499.00",
            "currency": "INR",
            "status": "failed",
            "payment_method": "upi",
            "transaction_timestamp": "2026-09-03T16:20:00Z",
            "metadata": {"source": "ml-api-test"},
        },
    )
    assert transaction_response.status_code == 201
    return merchant_id, transaction_response.json()["id"]


def analysis_payload(transaction_id: str | None = None):
    payload = {
        "transaction_id": transaction_id,
        "amount": "2499.00",
        "currency": "INR",
        "payment_method": "upi",
        "transaction_hour": 23,
        "day_of_week": 4,
        "customer_transaction_count": 8,
        "customer_avg_amount": "1800.00",
        "merchant_avg_amount": "2100.00",
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
        "customer_value": "14500.00",
        "previous_successful_payments": 7,
        "recovery_attempts": 1,
    }
    return payload


def test_risk_analyze_persists_score_and_summary(client):
    _, transaction_id = create_merchant_and_transaction(client)

    response = client.post("/api/v1/risk/analyze", json=analysis_payload(transaction_id))
    summary = client.get("/api/v1/risk/summary")

    assert response.status_code == 200
    assert 0 <= response.json()["risk_score"] <= 1
    assert summary.status_code == 200
    assert summary.json()["total_risk_scores"] == 1


def test_recovery_analyze_persists_opportunity_and_summary(client):
    _, transaction_id = create_merchant_and_transaction(client)

    response = client.post("/api/v1/recovery/analyze", json=analysis_payload(transaction_id))
    summary = client.get("/api/v1/recovery/summary")

    assert response.status_code == 200
    assert Decimal(response.json()["expected_recovered_value"]) >= Decimal("0")
    assert summary.status_code == 200
    assert summary.json()["total_opportunities"] == 1

