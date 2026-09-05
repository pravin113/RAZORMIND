from app.services.razorpay_service import (
    RazorpayConfigurationError,
    RazorpayServiceError,
    get_razorpay_service,
)
from app.main import app


class FakeRazorpayService:
    configured = True

    def create_order(self, amount, currency="INR", receipt=None, notes=None):
        return {
            "id": "order_test_123",
            "entity": "order",
            "amount": amount,
            "amount_paid": 0,
            "amount_due": amount,
            "currency": currency,
            "receipt": receipt,
            "status": "created",
            "attempts": 0,
            "notes": notes or {},
            "created_at": 1790000000,
        }

    def fetch_order(self, order_id):
        return {
            "id": order_id,
            "entity": "order",
            "amount": 29900,
            "amount_paid": 0,
            "amount_due": 29900,
            "currency": "INR",
            "receipt": "rm_test_001",
            "status": "created",
            "attempts": 0,
            "notes": {},
            "created_at": 1790000000,
        }

    def fetch_payment(self, payment_id):
        return {
            "id": payment_id,
            "entity": "payment",
            "amount": 29900,
            "currency": "INR",
            "status": "captured",
            "order_id": "order_test_123",
            "method": "upi",
            "captured": True,
            "created_at": 1790000000,
            "notes": {},
        }

    def fetch_order_payments(self, order_id):
        return {"count": 1, "items": [self.fetch_payment("pay_test_123")]}


class FailingRazorpayService(FakeRazorpayService):
    def create_order(self, amount, currency="INR", receipt=None, notes=None):
        raise RazorpayServiceError("boom")


class MissingCredentialsService(FakeRazorpayService):
    configured = False

    def create_order(self, amount, currency="INR", receipt=None, notes=None):
        raise RazorpayConfigurationError("missing")


def test_razorpay_status_when_configured(client):
    app.dependency_overrides[get_razorpay_service] = lambda: FakeRazorpayService()

    response = client.get("/api/v1/razorpay/status")

    assert response.status_code == 200
    assert response.json() == {"configured": True, "mode": "test"}


def test_razorpay_status_when_not_configured(client):
    app.dependency_overrides[get_razorpay_service] = lambda: MissingCredentialsService()

    response = client.get("/api/v1/razorpay/status")

    assert response.status_code == 200
    assert response.json() == {"configured": False, "mode": "test"}


def test_create_order_success(client):
    app.dependency_overrides[get_razorpay_service] = lambda: FakeRazorpayService()

    response = client.post(
        "/api/v1/razorpay/orders",
        json={"amount": 29900, "currency": "INR", "receipt": "rm_test_001", "notes": {"source": "razormind"}},
    )

    assert response.status_code == 201
    assert response.json()["id"] == "order_test_123"


def test_create_order_api_failure(client):
    app.dependency_overrides[get_razorpay_service] = lambda: FailingRazorpayService()

    response = client.post("/api/v1/razorpay/orders", json={"amount": 29900})

    assert response.status_code == 502


def test_fetch_order(client):
    app.dependency_overrides[get_razorpay_service] = lambda: FakeRazorpayService()

    response = client.get("/api/v1/razorpay/orders/order_test_123")

    assert response.status_code == 200
    assert response.json()["id"] == "order_test_123"


def test_fetch_payment(client):
    app.dependency_overrides[get_razorpay_service] = lambda: FakeRazorpayService()

    response = client.get("/api/v1/razorpay/payments/pay_test_123")

    assert response.status_code == 200
    assert response.json()["id"] == "pay_test_123"


def test_fetch_order_payments(client):
    app.dependency_overrides[get_razorpay_service] = lambda: FakeRazorpayService()

    response = client.get("/api/v1/razorpay/orders/order_test_123/payments")

    assert response.status_code == 200
    assert response.json()["count"] == 1

