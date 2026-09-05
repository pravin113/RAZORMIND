from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.ai.rag.embeddings import cosine_similarity, generate_embedding
from app.ai.rag.schemas import DocumentIngestRequest, RAGQueryRequest
from app.ai.rag.service import chunk_text, ingest_document, search_knowledge
from app.db.models import Merchant


def test_chunk_text_basic():
    short_text = "This is a short policy statement."
    chunks = chunk_text(short_text, chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0] == short_text

    long_text = "Paragraph 1 is about payment retries.\n\nParagraph 2 covers customer communication rules.\n\nParagraph 3 handles refund limits."
    chunks = chunk_text(long_text, chunk_size=50, overlap=10)
    assert len(chunks) >= 2


def test_embedding_and_similarity():
    text1 = "Payment failed due to temporary bank network outage."
    text2 = "Transaction failed because the issuing bank was unreachable."
    text3 = "The recipe requires two cups of flour and three eggs."

    emb1 = generate_embedding(text1)
    emb2 = generate_embedding(text2)
    emb3 = generate_embedding(text3)

    assert len(emb1) == 128
    assert len(emb2) == 128
    assert len(emb3) == 128

    sim_same = cosine_similarity(emb1, emb1)
    assert pytest.approx(sim_same, rel=1e-3) == 1.0

    sim_related = cosine_similarity(emb1, emb2)
    sim_unrelated = cosine_similarity(emb1, emb3)

    # Similar financial failure texts should score higher than baking recipe
    assert sim_related > sim_unrelated


def test_rag_ingest_and_retrieval(db_session):
    merchant = Merchant(
        name="RAG Merchant",
        email=f"rag_{uuid4().hex[:8]}@example.com",
        business_type="saas",
        currency="INR",
    )
    db_session.add(merchant)
    db_session.commit()

    # Ingest document
    doc_req = DocumentIngestRequest(
        merchant_id=merchant.id,
        title="Payment Retry and Refund Policy",
        document_type="retry_policy",
        content=(
            "Failed subscription payments may be retried up to 2 times within 48 hours. "
            "Customers should receive an email reminder before the second attempt. "
            "Refund requests must be processed within 5 business days for eligible disputes."
        ),
    )
    doc = ingest_document(db_session, doc_req)
    assert doc.id is not None
    assert doc.metadata_["chunk_count"] >= 1

    # Search relevant query
    query_req = RAGQueryRequest(
        query="What is the retry rule for failed subscriptions?",
        merchant_id=merchant.id,
        top_k=2,
    )
    results = search_knowledge(db_session, query_req)
    assert len(results) >= 1
    assert "retried up to 2 times" in results[0].chunk_text
    assert results[0].score > 0.5


def test_rag_merchant_isolation(db_session):
    merchant_a = Merchant(
        name="Merchant Alpha",
        email=f"alpha_{uuid4().hex[:8]}@example.com",
        business_type="retail",
        currency="INR",
    )
    merchant_b = Merchant(
        name="Merchant Beta",
        email=f"beta_{uuid4().hex[:8]}@example.com",
        business_type="retail",
        currency="INR",
    )
    db_session.add_all([merchant_a, merchant_b])
    db_session.commit()

    # Ingest private policy for Alpha
    ingest_document(
        db_session,
        DocumentIngestRequest(
            merchant_id=merchant_a.id,
            title="Alpha VIP Refund Terms",
            document_type="refund_policy",
            content="Alpha merchant permits instant refunds up to ₹50,000 for gold VIP members.",
        ),
    )

    # Query as Merchant Beta
    beta_results = search_knowledge(
        db_session,
        RAGQueryRequest(
            query="VIP refunds terms",
            merchant_id=merchant_b.id,
            top_k=5,
        ),
    )
    # Merchant Beta must NOT see Alpha's confidential policy
    assert len(beta_results) == 0


def test_rag_api_endpoints(client: TestClient, db_session):
    merchant = Merchant(
        name="API RAG Merchant",
        email=f"api_rag_{uuid4().hex[:8]}@example.com",
        business_type="ecommerce",
        currency="INR",
    )
    db_session.add(merchant)
    db_session.commit()

    # Ingest via API
    res = client.post(
        "/api/v1/rag/documents",
        json={
            "merchant_id": str(merchant.id),
            "title": "Customer Escalation Rules",
            "document_type": "escalation_rules",
            "content": "All transactions flagged as high risk must be escalated to level 2 fraud operations.",
        },
    )
    assert res.status_code == 201
    assert res.json()["title"] == "Customer Escalation Rules"

    # Query via API
    res = client.post(
        "/api/v1/rag/query",
        json={
            "query": "How to handle high risk transactions?",
            "merchant_id": str(merchant.id),
            "top_k": 3,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) >= 1
    assert "escalated to level 2" in data["results"][0]["chunk_text"]
