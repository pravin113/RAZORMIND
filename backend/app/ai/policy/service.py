from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.policy.engine import PolicyEngine
from app.ai.policy.schemas import (
    PolicyConfig,
    PolicyCreate,
    PolicyEvaluationRequest,
    PolicyEvaluationResponse,
    PolicyUpdate,
)
from app.db.models import Policy

logger = logging.getLogger(__name__)


def create_policy(db: Session, payload: PolicyCreate) -> Policy:
    config_dict = (
        payload.configuration.model_dump()
        if isinstance(payload.configuration, PolicyConfig)
        else payload.configuration
    )

    policy = Policy(
        merchant_id=payload.merchant_id,
        policy_name=payload.policy_name,
        policy_type=payload.policy_type,
        configuration=config_dict,
        enabled=payload.enabled,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def get_policy(db: Session, policy_id: UUID) -> Policy | None:
    return db.get(Policy, policy_id)


def get_merchant_policy(
    db: Session, merchant_id: UUID, policy_type: str = "recovery"
) -> Policy | None:
    stmt = (
        select(Policy)
        .where(
            Policy.merchant_id == merchant_id,
            Policy.policy_type == policy_type,
            Policy.enabled.is_(True),
        )
        .order_by(Policy.created_at.desc())
    )
    return db.scalars(stmt).first()


def list_policies(
    db: Session,
    merchant_id: UUID | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[Policy]:
    stmt = select(Policy)
    if merchant_id:
        stmt = stmt.where(Policy.merchant_id == merchant_id)
    stmt = stmt.order_by(Policy.created_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def update_policy(db: Session, policy_id: UUID, payload: PolicyUpdate) -> Policy | None:
    policy = db.get(Policy, policy_id)
    if not policy:
        return None

    if payload.policy_name is not None:
        policy.policy_name = payload.policy_name
    if payload.configuration is not None:
        policy.configuration = payload.configuration
    if payload.enabled is not None:
        policy.enabled = payload.enabled

    db.commit()
    db.refresh(policy)
    return policy


def evaluate_merchant_policy(
    db: Session, request: PolicyEvaluationRequest
) -> PolicyEvaluationResponse:
    policy = get_merchant_policy(db, request.merchant_id, policy_type="recovery")
    if policy:
        return PolicyEngine.evaluate(
            request=request,
            config=policy.configuration,
            policy_id=str(policy.id),
        )

    # If no specific merchant policy configured, evaluate against safe default policy
    default_config = PolicyConfig()
    return PolicyEngine.evaluate(
        request=request,
        config=default_config,
        policy_id=None,
    )
