from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.rag.embeddings import generate_embedding
from app.ai.rag.retriever import retrieve_relevant_chunks
from app.ai.rag.schemas import DocumentIngestRequest, RAGQueryRequest, RAGSearchResult
from app.db.models import Document

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """Split text into manageable overlapping chunks based on sentence/paragraph breaks."""
    clean = text.strip()
    if not clean:
        return []
    if len(clean) <= chunk_size:
        return [clean]

    paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current_chunk = ""

    for p in paragraphs:
        if len(current_chunk) + len(p) + 2 <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{p}".strip() if current_chunk else p
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(p) <= chunk_size:
                current_chunk = p
            else:
                # Break long paragraph
                start = 0
                while start < len(p):
                    end = start + chunk_size
                    chunks.append(p[start:end])
                    start += chunk_size - overlap
                current_chunk = ""

    if current_chunk:
        chunks.append(current_chunk)

    return chunks or [clean]


def ingest_document(db: Session, request: DocumentIngestRequest) -> Document:
    """Ingest, chunk, embed, and persist a merchant knowledge document."""
    raw_chunks = chunk_text(request.content)
    processed_chunks = []

    for i, chunk_str in enumerate(raw_chunks):
        emb = generate_embedding(chunk_str)
        processed_chunks.append({
            "chunk_index": i,
            "text": chunk_str,
            "embedding": emb,
        })

    metadata_payload = {
        "chunks": processed_chunks,
        "chunk_count": len(processed_chunks),
        "custom_meta": request.metadata,
    }

    doc = Document(
        merchant_id=request.merchant_id,
        title=request.title,
        content=request.content,
        document_type=request.document_type,
        metadata_=metadata_payload,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    logger.info("Ingested document %s (%d chunks) for merchant %s", doc.id, len(processed_chunks), doc.merchant_id)
    return doc


def search_knowledge(db: Session, request: RAGQueryRequest) -> list[RAGSearchResult]:
    """Search knowledge documents for relevant chunks."""
    return retrieve_relevant_chunks(
        db=db,
        query=request.query,
        merchant_id=request.merchant_id,
        document_type=request.document_type,
        top_k=request.top_k,
    )


def get_rag_context_for_prompt(
    db: Session, query: str, merchant_id: UUID | None, top_k: int = 3
) -> str:
    """Format relevant merchant knowledge snippets for inclusion in Qwen prompts/tools."""
    results = retrieve_relevant_chunks(
        db=db,
        query=query,
        merchant_id=merchant_id,
        top_k=top_k,
    )
    if not results:
        return ""

    snippets = []
    for r in results:
        snippets.append(f"[{r.document_type.upper()}] {r.title}:\n{r.chunk_text}")
    return "\n\nRelevant Merchant Policies & Context:\n" + "\n---\n".join(snippets)
