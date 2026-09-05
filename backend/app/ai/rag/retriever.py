from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.ai.rag.embeddings import cosine_similarity, generate_embedding
from app.ai.rag.schemas import RAGSearchResult
from app.db.models import Document


def retrieve_relevant_chunks(
    db: Session,
    query: str,
    merchant_id: UUID | None = None,
    document_type: str | None = None,
    top_k: int = 3,
    min_score: float = 0.50,
) -> list[RAGSearchResult]:
    """Retrieve top-K matching knowledge chunks with strict merchant isolation."""
    query_vector = generate_embedding(query)

    # Merchant isolation: return merchant documents or general platform policies (merchant_id is None)
    stmt = select(Document)
    if merchant_id is not None:
        stmt = stmt.where(
            or_(
                Document.merchant_id == merchant_id,
                Document.merchant_id.is_(None),
            )
        )
    else:
        stmt = stmt.where(Document.merchant_id.is_(None))

    if document_type:
        stmt = stmt.where(Document.document_type == document_type)

    documents = db.scalars(stmt).all()
    results: list[RAGSearchResult] = []

    for doc in documents:
        meta = doc.metadata_ or {}
        chunks = meta.get("chunks", [])

        # If chunks exist in metadata
        if chunks and isinstance(chunks, list):
            for chunk in chunks:
                chunk_text = chunk.get("text", "")
                chunk_emb = chunk.get("embedding", [])
                score = cosine_similarity(query_vector, chunk_emb) if chunk_emb else 0.0
                if score >= min_score:
                    results.append(
                        RAGSearchResult(
                            document_id=str(doc.id),
                            merchant_id=str(doc.merchant_id) if doc.merchant_id else None,
                            title=doc.title,
                            document_type=doc.document_type,
                            chunk_text=chunk_text,
                            score=round(score, 4),
                            metadata=meta.get("custom_meta", {}),
                        )
                    )
        else:
            # Fallback if document wasn't pre-chunked
            doc_emb = meta.get("embedding")
            if not doc_emb:
                doc_emb = generate_embedding(doc.content)
            score = cosine_similarity(query_vector, doc_emb)
            if score >= min_score:
                results.append(
                    RAGSearchResult(
                        document_id=str(doc.id),
                        merchant_id=str(doc.merchant_id) if doc.merchant_id else None,
                        title=doc.title,
                        document_type=doc.document_type,
                        chunk_text=doc.content[:500],
                        score=round(score, 4),
                        metadata=meta.get("custom_meta", {}),
                    )
                )

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]
