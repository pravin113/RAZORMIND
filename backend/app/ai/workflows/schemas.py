from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkflowExecuteRequest(BaseModel):
    merchant_id: UUID = Field(..., description="Target merchant UUID")
    transaction_id: UUID | None = Field(default=None, description="Optional transaction UUID")
    opportunity_id: UUID | None = Field(default=None, description="Optional recovery opportunity UUID")
    dry_run: bool = Field(default=False, description="Simulate without mutating state")


class ProposedDecision(BaseModel):
    action: str = Field(..., description="Proposed action: retry_payment, send_payment_reminder, create_followup, escalate_to_human, no_action")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Decision confidence")
    reason: str = Field(..., description="Rationale for the chosen action")
    expected_recovery: float = Field(default=0.0, description="Estimated recovery amount in INR")


class WorkflowPolicyResult(BaseModel):
    decision: str = Field(..., description="ALLOW, DENY, or REQUIRE_REVIEW")
    reason: str = Field(..., description="Policy evaluation summary")
    policy_id: str | None = Field(default=None, description="ID of governing policy if configured")
    checks: dict[str, bool] = Field(default_factory=dict, description="Detailed policy check results")


class WorkflowExecutionResult(BaseModel):
    status: str = Field(..., description="Execution status: success, blocked, skipped, failed")
    action_type: str = Field(..., description="Action attempted")
    details: dict[str, Any] = Field(default_factory=dict, description="Safe execution details")


class WorkflowVerificationResult(BaseModel):
    status: str = Field(..., description="Outcome status: recovered, stopped, queued_for_review, failed, pending")
    details: dict[str, Any] = Field(default_factory=dict, description="Verification details")


class WorkflowExecuteResponse(BaseModel):
    workflow_id: str
    status: str
    merchant_id: str
    transaction_id: str | None = None
    opportunity_id: str | None = None
    decision: ProposedDecision
    policy: WorkflowPolicyResult
    execution: WorkflowExecutionResult
    verification: WorkflowVerificationResult
    amount_recovered: float = 0.0
    tools_used: list[str] = Field(default_factory=list)
    outcome_id: str | None = None
    created_at: str


class RecoveryOutcomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    opportunity_id: UUID
    merchant_id: UUID
    predicted_probability: float
    chosen_action: str
    policy_decision: str
    actual_result: str
    recovered_amount: float
    attempt_number: int
    prediction_correctness: bool | None = None
    created_at: datetime
