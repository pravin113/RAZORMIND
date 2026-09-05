import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8000"


def request(method: str, path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(
        f"{BASE_URL}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8")
            return {"status_code": response.status, "body": json.loads(body)}
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        return {"status_code": exc.code, "body": json.loads(body)}


def main() -> None:
    merchant = request(
        "POST",
        "/api/v1/merchants",
        {
            "name": "Smoke Test Merchant",
            "email": "smoke@example.test",
            "business_type": "saas",
            "currency": "INR",
        },
    )["body"]
    transaction = request(
        "POST",
        "/api/v1/transactions",
        {
            "merchant_id": merchant["id"],
            "amount": "2499.00",
            "currency": "INR",
            "status": "failed",
            "payment_method": "upi",
            "transaction_timestamp": "2026-09-03T16:20:00Z",
            "metadata": {"source": "smoke-test"},
        },
    )["body"]
    analysis_payload = {
        "transaction_id": transaction["id"],
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
    results = {
        "health": request("GET", "/api/v1/health"),
        "db_health": request("GET", "/api/v1/db/health"),
        "risk_analyze": request("POST", "/api/v1/risk/analyze", analysis_payload),
        "recovery_analyze": request("POST", "/api/v1/recovery/analyze", analysis_payload),
        "risk_summary": request("GET", "/api/v1/risk/summary"),
        "recovery_summary": request("GET", "/api/v1/recovery/summary"),
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

