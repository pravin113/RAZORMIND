from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentIngestRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    content: str = Field(..., min_length=1, description="Document body / rules")
    document_type: str = Field(
        default="policy",
        description="Type: refund_policy, retry_policy, communication_rules, escalation_rules, etc.",
    )
    merchant_id: UUID | None = Field(default=None, description="Optional merchant UUID for merchant-specific policy")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DocumentChunk(BaseModel):
    chunk_index: int
    text: str
    embedding: list[float] = Field(default_factory=list)


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query or rule inquiry")
    merchant_id: UUID | None = Field(default=None, description="Scope search to specific merchant")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of results to return")
    document_type: str | None = Field(default=None, description="Optional document type filter")


class RAGSearchResult(BaseModel):
    document_id: str
    merchant_id: str | None
    title: str
    document_type: str
    chunk_text: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGQueryResponse(BaseModel):
    query: str
    results: list[RAGSearchResult]
