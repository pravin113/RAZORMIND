from datetime import datetime, timezone
from decimal import Decimal

from app.schemas.audit import AuditLogCreate
from app.schemas.recovery import RecoveryOpportunityCreate
from app.schemas.risk import RiskScoreCreate
from app.services.audit_logs import create_audit_log
from app.services.recovery import create_recovery_opportunity
from app.services.risk_scores import create_risk_score


def create_test_merchant(client):
    response = client.post(
        "/api/v1/merchants",
        json={
            "name": "Acme Retail",
            "email": "ops@acme.test",
            "business_type": "retail",
            "currency": "INR",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_test_transaction(client, merchant_id: str):
    response = client.post(
        "/api/v1/transactions",
        json={
            "merchant_id": merchant_id,
            "amount": "1499.00",
            "currency": "INR",
            "status": "captured",
            "payment_method": "upi",
            "transaction_timestamp": "2026-09-03T16:20:00Z",
            "metadata": {"source": "pytest"},
        },
    )
    assert response.status_code == 201
    return response.json()


def test_database_health_returns_configured_status(client):
    response = client.get("/api/v1/db/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "configured": True,
        "database": "reachable",
    }


def test_create_and_list_merchants(client):
    merchant = create_test_merchant(client)

    response = client.get("/api/v1/merchants")

    assert response.status_code == 200
    assert response.json()[0]["id"] == merchant["id"]
    assert response.json()[0]["email"] == "ops@acme.test"


def test_create_list_and_get_transactions(client):
    merchant = create_test_merchant(client)
    transaction = create_test_transaction(client, merchant["id"])

    list_response = client.get("/api/v1/transactions")
    detail_response = client.get(f"/api/v1/transactions/{transaction['id']}")

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == transaction["id"]
    assert detail_response.status_code == 200
    assert detail_response.json()["metadata"] == {"source": "pytest"}


def test_get_transaction_returns_404_for_missing_id(client):
    response = client.get("/api/v1/transactions/11111111-1111-1111-1111-111111111111")

    assert response.status_code == 404


def test_list_risk_scores_for_transaction(client, db_session):
    merchant = create_test_merchant(client)
    transaction = create_test_transaction(client, merchant["id"])
    create_risk_score(
        db_session,
        RiskScoreCreate(
            transaction_id=transaction["id"],
            fraud_probability=Decimal("0.1200"),
            anomaly_score=Decimal("0.3400"),
            risk_score=Decimal("0.2200"),
            risk_level="low",
            model_version="stub-v1",
        ),
    )

    response = client.get(f"/api/v1/risk/scores/{transaction['id']}")

    assert response.status_code == 200
    assert response.json()[0]["risk_level"] == "low"


def test_list_recovery_opportunities(client, db_session):
    merchant = create_test_merchant(client)
    transaction = create_test_transaction(client, merchant["id"])
    create_recovery_opportunity(
        db_session,
        RecoveryOpportunityCreate(
            transaction_id=transaction["id"],
            opportunity_type="failed_payment_retry",
            amount_at_risk=Decimal("1499.00"),
            recovery_probability=Decimal("0.6500"),
            priority="high",
            status="open",
            recommended_action="Send payment retry reminder",
        ),
    )

    response = client.get("/api/v1/recovery/opportunities")

    assert response.status_code == 200
    assert response.json()[0]["status"] == "open"


def test_list_audit_logs(client, db_session):
    merchant = create_test_merchant(client)
    create_audit_log(
        db_session,
        AuditLogCreate(
            merchant_id=merchant["id"],
            actor_type="system",
            actor_id="pytest",
            action="create",
            resource_type="merchant",
            resource_id=merchant["id"],
            decision="allowed",
            reason="test seed",
            metadata={"test": True},
        ),
    )

    response = client.get("/api/v1/audit/logs")

    assert response.status_code == 200
    assert response.json()[0]["metadata"] == {"test": True}

