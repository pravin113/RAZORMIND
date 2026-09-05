from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.ai.rag.schemas import DocumentIngestRequest, RAGQueryRequest, RAGQueryResponse
from app.ai.rag.service import ingest_document, search_knowledge
from app.db.session import get_db

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def ingest_knowledge_document(
    payload: DocumentIngestRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    doc = ingest_document(db, payload)
    return {
        "id": str(doc.id),
        "merchant_id": str(doc.merchant_id) if doc.merchant_id else None,
        "title": doc.title,
        "document_type": doc.document_type,
        "chunk_count": doc.metadata_.get("chunk_count", 1) if doc.metadata_ else 1,
        "created_at": doc.created_at.isoformat(),
    }


@router.post("/query", response_model=RAGQueryResponse)
async def query_knowledge_base(
    payload: RAGQueryRequest,
    db: Session = Depends(get_db),
) -> RAGQueryResponse:
    results = search_knowledge(db, payload)
    return RAGQueryResponse(query=payload.query, results=results)
