from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agent.tools.base import ToolDefinition
from app.ai.rag.schemas import RAGQueryRequest
from app.ai.rag.service import search_knowledge


def search_merchant_knowledge(
    db: Session,
    query: str,
    merchant_id: str | None = None,
    document_type: str | None = None,
) -> dict[str, Any]:
    """Search merchant policy documents and rules (refunds, retries, communication, escalation)."""
    m_uuid = None
    if merchant_id:
        try:
            m_uuid = UUID(merchant_id)
        except (ValueError, TypeError):
            pass

    req = RAGQueryRequest(
        query=query,
        merchant_id=m_uuid,
        document_type=document_type,
        top_k=3,
    )
    results = search_knowledge(db, req)
    return {
        "query": query,
        "results_found": len(results),
        "results": [
            {
                "title": r.title,
                "document_type": r.document_type,
                "text": r.chunk_text,
                "relevance_score": r.score,
            }
            for r in results
        ],
    }


tool_search_merchant_knowledge = ToolDefinition(
    name="search_merchant_knowledge",
    description="Search merchant-specific policies, recovery guidelines, refund policies, communication rules, and escalation limits using RAG.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query or policy question",
            },
            "merchant_id": {
                "type": "string",
                "description": "Optional merchant UUID to isolate search to that merchant's policies",
            },
            "document_type": {
                "type": "string",
                "description": "Optional document filter (e.g. refund_policy, retry_policy, escalation_rules)",
            },
        },
        "required": ["query"],
    },
    func=search_merchant_knowledge,
)
