from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Merchant query or message")
    merchant_id: UUID | None = Field(default=None, description="Optional merchant ID for scoped intelligence")
    session_id: str | None = Field(default=None, description="Optional conversation session ID for multi-turn context")


class AgentChatResponse(BaseModel):
    answer: str = Field(..., description="Final response and explanation from the AI agent")
    tools_used: list[str] = Field(default_factory=list, description="List of tools invoked during reasoning")
    model: str = Field(default="Qwen3-8B", description="Model name used for generation")
    agent_id: str = Field(default="razormind-agent-v1", description="Identifier of the agent")
    decision_id: str = Field(..., description="ID of the recorded agent decision in the database")
    session_id: str | None = Field(default=None, description="Conversation session ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Safe execution metadata")
