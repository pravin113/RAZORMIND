from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.schemas.common import ORMModel


class TransactionAnalysisInput(ORMModel):
    transaction_id: UUID | None = None
    merchant_id: UUID | None = None
    customer_id: UUID | None = None
    amount: Decimal
    currency: str = "INR"
    payment_method: str
    transaction_hour: int
    day_of_week: int
    customer_transaction_count: int = 1
    customer_avg_amount: Decimal | None = None
    merchant_avg_amount: Decimal | None = None
    amount_deviation: float = 0.0
    customer_age_days: int = 0
    failed_attempts: int = 0
    device_change: int = 0
    ip_change: int = 0
    country_change: int = 0
    velocity_1h: int = 0
    velocity_24h: int = 0
    previous_chargebacks: int = 0
    previous_fraud_events: int = 0
    checkout_duration: float = 0.0
    retry_count: int = 0
    subscription: int = 0
    transaction_status: str = "captured"
    payment_failure: int = 0
    failure_reason: str = "none"
    subscription_status: str = "none"
    customer_value: Decimal = Decimal("0")
    previous_successful_payments: int = 0
    recovery_attempts: int = 0


class RiskAnalysisResponse(ORMModel):
    fraud_probability: float
    anomaly_score: float
    anomaly_flag: bool
    business_rule_score: float
    risk_score: float
    risk_level: str
    model_version: str


class RecoveryAnalysisResponse(ORMModel):
    recovery_probability: float
    expected_recovered_value: Decimal
    recommended_priority: str
    model_version: str


class RiskSummary(ORMModel):
    total_risk_scores: int
    average_risk_score: float
    by_risk_level: dict[str, int]


class RecoverySummary(ORMModel):
    total_opportunities: int
    open_opportunities: int
    average_recovery_probability: float
    expected_recovered_value: Decimal

