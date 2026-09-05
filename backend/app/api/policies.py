from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.ai.policy.schemas import (
    PolicyCreate,
    PolicyEvaluationRequest,
    PolicyEvaluationResponse,
    PolicyRead,
    PolicyUpdate,
)
from app.ai.policy.service import (
    create_policy,
    evaluate_merchant_policy,
    get_policy,
    list_policies,
    update_policy,
)
from app.db.session import get_db

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("", response_model=list[PolicyRead])
async def list_merchant_policies(
    merchant_id: UUID | None = Query(default=None, description="Optional merchant UUID to filter policies"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_policies(db, merchant_id=merchant_id, offset=offset, limit=limit)


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
async def create_merchant_policy(
    payload: PolicyCreate,
    db: Session = Depends(get_db),
):
    return create_policy(db, payload)


@router.get("/{policy_id}", response_model=PolicyRead)
async def get_policy_by_id(
    policy_id: UUID,
    db: Session = Depends(get_db),
):
    policy = get_policy(db, policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return policy


@router.put("/{policy_id}", response_model=PolicyRead)
async def update_merchant_policy(
    policy_id: UUID,
    payload: PolicyUpdate,
    db: Session = Depends(get_db),
):
    updated = update_policy(db, policy_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return updated


@router.post("/evaluate", response_model=PolicyEvaluationResponse)
async def evaluate_action_policy(
    payload: PolicyEvaluationRequest,
    db: Session = Depends(get_db),
):
    return evaluate_merchant_policy(db, payload)
