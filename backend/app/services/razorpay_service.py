from __future__ import annotations

from typing import Any

import razorpay

from app.core.config import settings


class RazorpayConfigurationError(RuntimeError):
    pass


class RazorpayServiceError(RuntimeError):
    pass


class RazorpayService:
    def __init__(self, key_id: str | None = None, key_secret: str | None = None):
        self.key_id = key_id if key_id is not None else settings.razorpay_key_id
        self.key_secret = key_secret if key_secret is not None else settings.razorpay_key_secret
        self._client = None

    @property
    def configured(self) -> bool:
        return bool(self.key_id and self.key_secret)

    @property
    def client(self):
        if not self.configured:
            raise RazorpayConfigurationError("Razorpay test credentials are not configured")
        if self._client is None:
            self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
        return self._client

    def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: str | None = None,
        notes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"amount": amount, "currency": currency}
        if receipt:
            payload["receipt"] = receipt
        if notes:
            payload["notes"] = notes
        return self._call(lambda: self.client.order.create(data=payload))

    def fetch_order(self, order_id: str) -> dict[str, Any]:
        return self._call(lambda: self.client.order.fetch(order_id))

    def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        return self._call(lambda: self.client.payment.fetch(payment_id))

    def fetch_order_payments(self, order_id: str) -> dict[str, Any]:
        return self._call(lambda: self.client.order.payments(order_id))

    def _call(self, operation):
        try:
            return operation()
        except RazorpayConfigurationError:
            raise
        except Exception as exc:
            raise RazorpayServiceError("Razorpay API request failed") from exc


def get_razorpay_service() -> RazorpayService:
    return RazorpayService()

