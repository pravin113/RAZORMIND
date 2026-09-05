from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.agent.agent import (
    AgentProcessingError,
    AgentServiceUnavailableError,
    RazorMindAgent,
    get_razormind_agent,
)
from app.db.models import AgentDecision, AuditLog, Merchant
from app.db.session import get_db
from app.schemas.agent import AgentChatRequest, AgentChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


def _resolve_merchant_id(db: Session, merchant_id: UUID | None) -> UUID:
    """Resolve a valid merchant UUID for database foreign key constraints."""
    if merchant_id:
        existing = db.get(Merchant, merchant_id)
        if existing:
            return existing.id

    # Fall back to existing merchant or create a default platform merchant
    first_merchant = db.scalar(select(Merchant).order_by(Merchant.created_at.asc()))
    if first_merchant:
        return first_merchant.id

    default_merchant = Merchant(
        name="Default Agent Merchant",
        email="agent-default@razormind.local",
        business_type="platform",
        currency="INR",
    )
    db.add(default_merchant)
    db.flush()
    return default_merchant.id


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    payload: AgentChatRequest,
    db: Session = Depends(get_db),
    agent: RazorMindAgent = Depends(get_razormind_agent),
):
    """Chat with RazorMind AI agent for financial, risk, and revenue recovery intelligence."""
    effective_merchant_id = _resolve_merchant_id(db, payload.merchant_id)

    try:
        result = agent.chat(
            message=payload.message,
            db=db,
            merchant_id=effective_merchant_id,
            session_id=payload.session_id,
        )
    except AgentServiceUnavailableError as exc:
        logger.warning("Agent service unavailable: %s", exc)
        # Record audit log for failed/unavailable invocation
        db.add(
            AuditLog(
                merchant_id=effective_merchant_id,
                actor_type="merchant_agent",
                actor_id="razormind_agent",
                action="chat_query",
                resource_type="agent_decision",
                decision="unavailable",
                reason=str(exc),
                metadata_={"query": payload.message, "status": "unavailable"},
            )
        )
        db.commit()
        raise HTTPException(
            status_code=503,
            detail=f"AI Agent service is currently unavailable: {str(exc)}",
        ) from exc
    except AgentProcessingError as exc:
        logger.error("Agent processing error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"AI Agent processing error: {str(exc)}",
        ) from exc

    # Persist structured agent decision
    summary_reasoning = f"Query: {payload.message[:250]} | Tools invoked: {', '.join(result.tools_used) if result.tools_used else 'none'}"
    decision = AgentDecision(
        merchant_id=effective_merchant_id,
        decision_type="merchant_chat_query",
        reasoning=summary_reasoning,
        recommended_action=result.answer[:1000],
        confidence=Decimal("0.9500"),
        policy_result={
            "query": payload.message,
            "tools_used": result.tools_used,
            "model": result.model,
            "status": "success",
            "session_id": result.session_id,
        },
    )
    db.add(decision)
    db.flush()

    # Record audit log
    audit = AuditLog(
        merchant_id=effective_merchant_id,
        actor_type="merchant_agent",
        actor_id="razormind_agent",
        action="chat_query",
        resource_type="agent_decision",
        resource_id=str(decision.id),
        decision="completed",
        reason=f"Processed query with {len(result.tools_used)} tools",
        metadata_={
            "query": payload.message,
            "tools_used": result.tools_used,
            "model": result.model,
            "status": "success",
            "decision_id": str(decision.id),
        },
    )
    db.add(audit)
    db.commit()

    return AgentChatResponse(
        answer=result.answer,
        tools_used=result.tools_used,
        model=result.model,
        agent_id="razormind-agent-v1",
        decision_id=str(decision.id),
        session_id=result.session_id,
        metadata=result.metadata,
    )
