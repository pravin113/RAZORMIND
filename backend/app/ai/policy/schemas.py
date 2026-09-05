from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_REVIEW = "REQUIRE_REVIEW"


class PolicyConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="Whether automated recovery policy is active")
    min_recovery_probability: float = Field(default=0.65, ge=0.0, le=1.0, description="Minimum ML recovery probability")
    max_recovery_amount: float = Field(default=10000.0, ge=0.0, description="Maximum amount eligible for automated recovery")
    max_attempts: int = Field(default=2, ge=1, le=10, description="Maximum retry/recovery attempts permitted")
    cooldown_minutes: int = Field(default=60, ge=0, description="Minimum minutes between subsequent attempts")
    allowed_actions: list[str] = Field(
        default_factory=lambda: ["retry_payment", "send_payment_reminder", "create_followup"],
        description="Permitted recovery action types",
    )
    risk_restrictions: list[str] = Field(
        default_factory=lambda: ["HIGH", "CRITICAL"],
        description="Risk tiers that require manual merchant review",
    )
    min_confidence: float = Field(default=0.70, ge=0.0, le=1.0, description="Minimum decision confidence required")
    custom_rules: dict[str, Any] = Field(default_factory=dict, description="Merchant-specific custom rule overrides")


class PolicyCreate(BaseModel):
    merchant_id: UUID
    policy_name: str = Field(..., min_length=1, max_length=255)
    policy_type: str = Field(default="recovery", max_length=100)
    configuration: dict[str, Any] | PolicyConfig = Field(default_factory=dict)
    enabled: bool = True


class PolicyUpdate(BaseModel):
    policy_name: str | None = None
    configuration: dict[str, Any] | None = None
    enabled: bool | None = None


class PolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    policy_name: str
    policy_type: str
    configuration: dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime


class PolicyChecks(BaseModel):
    enabled: bool = True
    amount_limit: bool = True
    probability_threshold: bool = True
    attempt_limit: bool = True
    cooldown: bool = True
    action_allowed: bool = True
    risk_acceptable: bool = True
    confidence_acceptable: bool = True


class PolicyEvaluationRequest(BaseModel):
    merchant_id: UUID
    action_type: str = Field(..., description="Action proposed by AI or workflow")
    amount: float = Field(..., ge=0.0, description="Amount involved in recovery (INR)")
    recovery_probability: float = Field(..., ge=0.0, le=1.0, description="ML-predicted recovery probability")
    attempt_number: int = Field(default=1, ge=0, description="Current attempt number")
    risk_level: str | None = Field(default=None, description="Risk level (LOW, MEDIUM, HIGH, CRITICAL)")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Confidence of proposed action")
    last_attempt_at: datetime | None = Field(default=None, description="Timestamp of previous attempt")


class PolicyEvaluationResponse(BaseModel):
    decision: PolicyDecision
    reason: str
    policy_id: str | None = None
    checks: PolicyChecks
