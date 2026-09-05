from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select

from app.ai.agent.agent import (
    AgentProcessingError,
    AgentServiceUnavailableError,
    RazorMindAgent,
    _parse_tool_arguments,
    _strip_chain_of_thought,
    get_razormind_agent,
)
from app.ai.agent.config import AgentConfig, get_agent_config
from app.ai.agent.tools import (
    ALL_TOOLS,
    get_default_tool_registry,
    tool_get_customer_history,
    tool_get_failed_payments,
    tool_get_payment_details,
    tool_get_policy,
    tool_get_recovery_probability,
    tool_get_recovery_summary,
    tool_get_revenue_metrics,
    tool_get_risk_score,
    tool_get_risk_summary,
    tool_get_transaction,
)
from app.core.config import settings
from app.db.models import (
    AgentDecision,
    AuditLog,
    Customer,
    FraudEvent,
    Merchant,
    PaymentAttempt,
    RecoveryOpportunity,
    RiskScore,
    Transaction,
)
from app.main import app


# ---------------------------------------------------------------------------
# Test Fixtures & Seed Helpers
# ---------------------------------------------------------------------------

def create_seed_data(db_session):
    merchant = Merchant(
        name="Test Merchant Corp",
        email="corp@test.local",
        business_type="saas",
        currency="INR",
    )
    db_session.add(merchant)
    db_session.flush()

    customer = Customer(
        merchant_id=merchant.id,
        external_customer_id="cust_ext_001",
        name="John Doe",
        email="john@example.com",
    )
    db_session.add(customer)
    db_session.flush()

    now = datetime.now(timezone.utc)

    # Successful Transaction
    tx_success = Transaction(
        merchant_id=merchant.id,
        customer_id=customer.id,
        razorpay_payment_id="pay_succ_101",
        amount=Decimal("4999.00"),
        currency="INR",
        status="captured",
        payment_method="upi",
        transaction_timestamp=now,
        metadata_={"source": "test"},
    )
    db_session.add(tx_success)

    # Failed Transaction
    tx_failed = Transaction(
        merchant_id=merchant.id,
        customer_id=customer.id,
        razorpay_payment_id="pay_fail_202",
        amount=Decimal("2499.00"),
        currency="INR",
        status="failed",
        payment_method="card",
        transaction_timestamp=now,
        metadata_={"source": "test"},
    )
    db_session.add(tx_failed)
    db_session.flush()

    # Payment Attempt for Failed Transaction
    attempt = PaymentAttempt(
        transaction_id=tx_failed.id,
        attempt_number=1,
        status="failed",
        failure_code="BAD_REQUEST_ERROR",
        failure_reason="Card expired",
        attempted_at=now,
    )
    db_session.add(attempt)

    # Risk Score for Failed Transaction
    risk = RiskScore(
        transaction_id=tx_failed.id,
        fraud_probability=Decimal("0.8500"),
        anomaly_score=Decimal("0.7200"),
        risk_score=Decimal("0.8000"),
        risk_level="HIGH",
        model_version="v1-test",
    )
    db_session.add(risk)
    db_session.flush()

    fraud = FraudEvent(
        transaction_id=tx_failed.id,
        risk_score=risk,
        event_type="ml_risk_flag",
        severity="HIGH",
        amount_at_risk=Decimal("2499.00"),
        reason="Suspicious card anomaly",
        status="open",
    )
    db_session.add(fraud)

    # Recovery Opportunity
    recovery = RecoveryOpportunity(
        transaction_id=tx_failed.id,
        customer_id=customer.id,
        opportunity_type="payment_recovery",
        amount_at_risk=Decimal("2499.00"),
        recovery_probability=Decimal("0.6500"),
        priority="high",
        status="open",
        recommended_action="Send card update payment link",
    )
    db_session.add(recovery)
    db_session.commit()

    return {
        "merchant": merchant,
        "customer": customer,
        "tx_success": tx_success,
        "tx_failed": tx_failed,
        "risk": risk,
        "recovery": recovery,
    }


# ---------------------------------------------------------------------------
# Unit Tests: Configuration & Initialization
# ---------------------------------------------------------------------------

def test_qwen_configuration():
    config = get_agent_config()
    assert config.model_name == "Qwen3-8B"
    assert config.temperature == 0.2
    assert config.max_tokens == 1024
    assert config.enabled is True
    assert "Qwen3-8B-Q4_K_M.gguf" in config.model_path


def test_agent_initialization():
    agent = RazorMindAgent()
    assert agent.config.model_name == "Qwen3-8B"
    assert len(agent.tool_registry.list_names()) == 13
    assert "get_transaction" in agent.tool_registry.list_names()
    assert "get_revenue_metrics" in agent.tool_registry.list_names()


def test_agent_disabled_behavior(db_session):
    disabled_config = AgentConfig(enabled=False)
    agent = RazorMindAgent(config=disabled_config)
    with pytest.raises(AgentServiceUnavailableError, match="disabled"):
        agent.chat("Why did revenue drop?", db=db_session)


def test_qwen_unavailable_behavior(db_session):
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = httpx.ConnectError("Connection refused")
    agent = RazorMindAgent(http_client=mock_client)

    with pytest.raises(AgentServiceUnavailableError, match="unreachable"):
        agent.chat("Why did revenue drop?", db=db_session)


# ---------------------------------------------------------------------------
# Unit Tests: Tool Registry & Individual Tools
# ---------------------------------------------------------------------------

def test_tool_registry():
    registry = get_default_tool_registry()
    tools = registry.to_openai_tools()
    assert len(tools) == 13
    names = [t["function"]["name"] for t in tools]
    assert "get_transaction" in names
    assert "get_customer_history" in names
    assert "get_risk_score" in names
    assert "get_recovery_probability" in names
    assert "get_revenue_metrics" in names
    assert "get_failed_payments" in names
    assert "get_risk_summary" in names
    assert "get_recovery_summary" in names
    assert "get_payment_details" in names
    assert "get_policy" in names
    assert "evaluate_recovery_policy" in names
    assert "execute_recovery_workflow" in names
    assert "search_merchant_knowledge" in names


def test_tool_get_transaction(db_session):
    data = create_seed_data(db_session)
    res = tool_get_transaction.func(db=db_session, transaction_id=str(data["tx_failed"].id))
    assert res["transaction_id"] == str(data["tx_failed"].id)
    assert res["amount"] == 2499.0
    assert res["status"] == "failed"
    assert res["failure_reason"] == "Card expired"

    # Missing transaction
    not_found = tool_get_transaction.func(db=db_session, transaction_id=str(uuid4()))
    assert "error" in not_found


def test_tool_get_customer_history(db_session):
    data = create_seed_data(db_session)
    res = tool_get_customer_history.func(db=db_session, customer_id=str(data["customer"].id))
    assert res["transaction_count"] == 2
    assert res["successful_payments"] == 1
    assert res["failed_payments"] == 1
    assert res["total_amount"] == 7498.0
    assert len(res["recovery_history"]) == 1


def test_tool_get_risk_score(db_session):
    data = create_seed_data(db_session)
    res = tool_get_risk_score.func(db=db_session, transaction_id=str(data["tx_failed"].id))
    assert res["risk_level"] == "HIGH"
    assert res["fraud_probability"] == 0.85
    assert len(res["fraud_events"]) == 1

    # Unscored transaction
    unscored = tool_get_risk_score.func(db=db_session, transaction_id=str(data["tx_success"].id))
    assert unscored["status"] == "not_scored"


def test_tool_get_recovery_probability(db_session):
    data = create_seed_data(db_session)
    res = tool_get_recovery_probability.func(db=db_session, transaction_id=str(data["tx_failed"].id))
    assert res["recovery_probability"] == 0.65
    assert res["amount_at_risk"] == 2499.0
    assert res["priority"] == "high"
    assert "Card update" in res["recommendation"] or "card" in res["recommendation"].lower()


def test_tool_get_revenue_metrics(db_session):
    create_seed_data(db_session)
    res = tool_get_revenue_metrics.func(db=db_session)
    assert res["transaction_count"] == 2
    assert res["total_revenue"] == 4999.0
    assert res["failed_payment_amount"] == 2499.0
    assert res["payment_success_rate"] == 0.5


def test_tool_get_failed_payments(db_session):
    create_seed_data(db_session)
    res = tool_get_failed_payments.func(db=db_session)
    assert res["count"] == 1
    assert res["payments"][0]["payment_method"] == "card"
    assert res["payments"][0]["failure_reason"] == "Card expired"


def test_tool_get_risk_summary(db_session):
    create_seed_data(db_session)
    res = tool_get_risk_summary.func(db=db_session)
    assert res["total_transactions_analyzed"] >= 1
    assert res["high_risk_count"] == 1


def test_tool_get_recovery_summary(db_session):
    create_seed_data(db_session)
    res = tool_get_recovery_summary.func(db=db_session)
    assert res["failed_payments"] == 1
    assert res["recovery_opportunities"] >= 1
    assert res["average_recovery_probability"] == 0.65


def test_tool_get_payment_details(db_session):
    data = create_seed_data(db_session)
    # Database fallback path
    res = tool_get_payment_details.func(db=db_session, razorpay_payment_id="pay_succ_101")
    assert res["source"] in ["database_fallback", "razorpay_api"]
    assert res["payment"]["id"] == "pay_succ_101"
    assert res["payment"]["amount"] == 4999.0


def test_tool_get_policy(db_session):
    res = tool_get_policy.func(db=db_session)
    assert res["status"] == "enforced"
    assert res["guardrails"]["automatic_refunds"] is False
    assert res["guardrails"]["automatic_payment_retries"] is False
    assert res["guardrails"]["account_blocking"] is False


def test_tool_validation(db_session):
    registry = get_default_tool_registry()
    # Unknown tool
    unknown = registry.execute("non_existent_tool", db=db_session)
    assert "error" in unknown

    # Invalid JSON string argument
    invalid_json = registry.execute("get_transaction", db=db_session, arguments="{bad-json")
    assert "error" in invalid_json


def test_phase6_agent_tools(db_session):
    data = create_seed_data(db_session)
    merchant = data["merchant"]
    tx_failed = data["tx_failed"]
    registry = get_default_tool_registry()

    # 1. evaluate_recovery_policy tool
    policy_eval = registry.execute(
        "evaluate_recovery_policy",
        db=db_session,
        arguments={
            "merchant_id": str(merchant.id),
            "action_type": "retry_payment",
            "amount": 2499.0,
            "recovery_probability": 0.80,
            "attempt_number": 1,
            "risk_level": "LOW",
        },
    )
    assert policy_eval["decision"] == "ALLOW"
    assert "checks" in policy_eval

    # 2. execute_recovery_workflow tool on high-risk/recent attempt tx -> evaluates and executes boundedly
    workflow_res = registry.execute(
        "execute_recovery_workflow",
        db=db_session,
        arguments={
            "merchant_id": str(merchant.id),
            "transaction_id": str(tx_failed.id),
        },
    )
    assert workflow_res["status"] == "completed"
    assert "workflow_id" in workflow_res
    assert workflow_res["policy_decision"] in ["ALLOW", "DENY", "REQUIRE_REVIEW"]

    # 3. search_merchant_knowledge tool
    rag_res = registry.execute(
        "search_merchant_knowledge",
        db=db_session,
        arguments={
            "query": "refund retry policy rules",
            "merchant_id": str(merchant.id),
        },
    )
    assert "results" in rag_res



# ---------------------------------------------------------------------------
# Integration Tests: Chat Endpoint, Tool Calling, Multi-Turn, Audit, Safety
# ---------------------------------------------------------------------------

class FakeLLMClient:
    """Mock HTTP client simulating OpenAI/Qwen tool calling and response synthesis."""

    def __init__(self, turns: list[dict]):
        self.turns = list(turns)
        self.call_count = 0

    def post(self, url, json=None, headers=None):
        if self.call_count < len(self.turns):
            resp_data = self.turns[self.call_count]
            self.call_count += 1
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = resp_data
            mock_resp.text = json if isinstance(json, str) else ""
            return mock_resp
        # Default fallback
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Default response."}}]
        }
        return mock_resp


def test_agent_chat_endpoint_success(client, db_session):
    create_seed_data(db_session)

    fake_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Your revenue dropped because card payment failures increased by ₹2,499.00.",
                }
            }
        ]
    }
    fake_client = FakeLLMClient([fake_response])
    app.dependency_overrides[get_razormind_agent] = lambda: RazorMindAgent(http_client=fake_client)

    try:
        resp = client.post("/api/v1/agent/chat", json={"message": "Why did my revenue drop this week?"})
        assert resp.status_code == 200
        data = resp.json()
        assert "revenue dropped" in data["answer"]
        assert data["model"] == "Qwen3-8B"
        assert data["agent_id"] == "razormind-agent-v1"
        assert "decision_id" in data
    finally:
        app.dependency_overrides.clear()


def test_agent_tool_calling_flow(client, db_session):
    create_seed_data(db_session)

    # Step 1: Model requests tool call 'get_revenue_metrics'
    step_1 = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_rev_001",
                            "type": "function",
                            "function": {
                                "name": "get_revenue_metrics",
                                "arguments": json.dumps({"start_date": "2026-09-01"}),
                            },
                        }
                    ],
                }
            }
        ]
    }
    # Step 2: Model uses tool results to produce final explanation
    step_2 = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Revenue for the period was ₹4,999.00 with ₹2,499.00 in failed payments.",
                }
            }
        ]
    }

    fake_client = FakeLLMClient([step_1, step_2])
    app.dependency_overrides[get_razormind_agent] = lambda: RazorMindAgent(http_client=fake_client)

    try:
        resp = client.post("/api/v1/agent/chat", json={"message": "Analyze my payment metrics"})
        assert resp.status_code == 200
        data = resp.json()
        assert "get_revenue_metrics" in data["tools_used"]
        assert "₹4,999.00" in data["answer"]
    finally:
        app.dependency_overrides.clear()


def test_agent_decision_persistence(client, db_session):
    create_seed_data(db_session)

    fake_response = {
        "choices": [{"message": {"role": "assistant", "content": "Recovery rate is currently 65%."}}]
    }
    fake_client = FakeLLMClient([fake_response])
    app.dependency_overrides[get_razormind_agent] = lambda: RazorMindAgent(http_client=fake_client)

    try:
        resp = client.post("/api/v1/agent/chat", json={"message": "What is our recovery potential?"})
        assert resp.status_code == 200
        decision_id = resp.json()["decision_id"]

        decision = db_session.scalar(select(AgentDecision).where(AgentDecision.id == decision_id))
        assert decision is not None
        assert decision.decision_type == "merchant_chat_query"
        assert decision.policy_result["query"] == "What is our recovery potential?"
        assert decision.policy_result["status"] == "success"
    finally:
        app.dependency_overrides.clear()


def test_agent_audit_logging(client, db_session):
    create_seed_data(db_session)

    fake_response = {
        "choices": [{"message": {"role": "assistant", "content": "Audit check response."}}]
    }
    fake_client = FakeLLMClient([fake_response])
    app.dependency_overrides[get_razormind_agent] = lambda: RazorMindAgent(http_client=fake_client)

    try:
        resp = client.post("/api/v1/agent/chat", json={"message": "Audit check query"})
        assert resp.status_code == 200
        decision_id = resp.json()["decision_id"]

        audit = db_session.scalar(
            select(AuditLog).where(
                AuditLog.actor_type == "merchant_agent",
                AuditLog.resource_id == decision_id,
            )
        )
        assert audit is not None
        assert audit.action == "chat_query"
        assert audit.decision == "completed"
        assert audit.metadata_["query"] == "Audit check query"
    finally:
        app.dependency_overrides.clear()


def test_no_secret_leakage_and_clean_reasoning():
    raw_content = "<think>Internal hidden chain of thought reasoning</think>Final merchant answer."
    cleaned = _strip_chain_of_thought(raw_content)
    assert cleaned == "Final merchant answer."
    assert "<think>" not in cleaned


def test_multi_turn_conversation_context(client, db_session):
    create_seed_data(db_session)

    # First turn
    turn_1 = {"choices": [{"message": {"role": "assistant", "content": "Revenue fell by 15%."}}]}
    # Second turn
    turn_2 = {"choices": [{"message": {"role": "assistant", "content": "We can recover up to ₹2,499."}}]}

    agent = RazorMindAgent(http_client=FakeLLMClient([turn_1, turn_2]))
    app.dependency_overrides[get_razormind_agent] = lambda: agent

    try:
        r1 = client.post(
            "/api/v1/agent/chat",
            json={"message": "Why did revenue drop?", "session_id": "sess_101"},
        )
        assert r1.status_code == 200
        assert r1.json()["session_id"] == "sess_101"

        r2 = client.post(
            "/api/v1/agent/chat",
            json={"message": "How much can we recover?", "session_id": "sess_101"},
        )
        assert r2.status_code == 200
        assert r2.json()["session_id"] == "sess_101"

        # Session history should have 4 messages (2 user, 2 assistant)
        history = agent.get_session_history("sess_101")
        assert len(history) == 4
        assert history[0]["content"] == "Why did revenue drop?"
        assert history[2]["content"] == "How much can we recover?"
    finally:
        app.dependency_overrides.clear()


def test_agent_chat_when_service_unavailable(client):
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = httpx.ConnectError("Connection refused")
    agent = RazorMindAgent(http_client=mock_client)
    app.dependency_overrides[get_razormind_agent] = lambda: agent

    try:
        resp = client.post("/api/v1/agent/chat", json={"message": "Check status"})
        assert resp.status_code == 503
        assert "unavailable" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_parse_tool_arguments():
    # 1. Empty JSON string
    assert _parse_tool_arguments("{}") == {}

    # 2. JSON string with fields
    assert _parse_tool_arguments('{"start_date": "2026-09-01", "limit": 10}') == {
        "start_date": "2026-09-01",
        "limit": 10,
    }

    # 3. Native dictionary
    assert _parse_tool_arguments({"transaction_id": "tx_123"}) == {"transaction_id": "tx_123"}

    # 4. Whitespace or empty string
    assert _parse_tool_arguments("") == {}
    assert _parse_tool_arguments("   ") == {}

    # 5. Invalid JSON string fallback
    assert _parse_tool_arguments("not-valid-json") == {}

    # 6. Non-string, non-dict fallback
    assert _parse_tool_arguments(None) == {}


def test_real_qwen_json_string_tool_call_flow(client, db_session):
    """Test the exact response format emitted by Qwen3-8B on llama-server with arguments as JSON string."""
    create_seed_data(db_session)

    # Step 1: Real Qwen3-8B response format from llama-server:
    # finish_reason: "tool_calls", function.arguments is "{}" string, reasoning_content present
    captured_messages_sent = []

    class CapturingLLMClient:
        def __init__(self):
            self.turn = 0

        def post(self, url, json=None, headers=None):
            captured_messages_sent.append(list(json.get("messages", [])))
            mock_resp = MagicMock()
            mock_resp.status_code = 200

            if self.turn == 0:
                self.turn += 1
                mock_resp.json.return_value = {
                    "choices": [
                        {
                            "finish_reason": "tool_calls",
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "",
                                "reasoning_content": "Okay, the user wants revenue metrics. I should call get_revenue_metrics with no arguments.",
                                "tool_calls": [
                                    {
                                        "id": "fH9aBDVEa1JatwbMJ9QPen7kX4YoWuFe",
                                        "type": "function",
                                        "function": {
                                            "name": "get_revenue_metrics",
                                            "arguments": "{}",  # Exact JSON string returned by Qwen
                                        },
                                    }
                                ],
                            },
                        }
                    ]
                }
                return mock_resp
            else:
                mock_resp.json.return_value = {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "Based on current data, your total revenue is ₹4,999.00.",
                                "reasoning_content": "Internal thought: I now have the data from the tool.",
                            },
                        }
                    ]
                }
                return mock_resp

    capturing_client = CapturingLLMClient()
    agent = RazorMindAgent(http_client=capturing_client)
    app.dependency_overrides[get_razormind_agent] = lambda: agent

    try:
        resp = client.post("/api/v1/agent/chat", json={"message": "What is my revenue?"})
        assert resp.status_code == 200
        data = resp.json()

        # Check tool execution
        assert "get_revenue_metrics" in data["tools_used"]
        assert "₹4,999.00" in data["answer"]
        assert "Internal thought" not in data["answer"]

        # Check that conversation was correctly formatted for turn 2
        assert len(captured_messages_sent) == 2
        second_turn_messages = captured_messages_sent[1]

        # The second turn messages should contain:
        # [0] system prompt
        # [1] user message
        # [2] assistant message with tool_calls (arguments MUST be string "{}" for OpenAI compatibility)
        # [3] tool message with role="tool", tool_call_id="fH9aBDVEa1JatwbMJ9QPen7kX4YoWuFe"
        assistant_turn_msg = second_turn_messages[2]
        assert assistant_turn_msg["role"] == "assistant"
        assert len(assistant_turn_msg["tool_calls"]) == 1
        assert assistant_turn_msg["tool_calls"][0]["id"] == "fH9aBDVEa1JatwbMJ9QPen7kX4YoWuFe"
        assert assistant_turn_msg["tool_calls"][0]["function"]["arguments"] == "{}"

        tool_result_msg = second_turn_messages[3]
        assert tool_result_msg["role"] == "tool"
        assert tool_result_msg["tool_call_id"] == "fH9aBDVEa1JatwbMJ9QPen7kX4YoWuFe"
        assert tool_result_msg["name"] == "get_revenue_metrics"
        tool_content = json.loads(tool_result_msg["content"])
        assert "total_revenue" in tool_content
        assert tool_content["total_revenue"] == 4999.0
    finally:
        app.dependency_overrides.clear()


def test_unclosed_think_tag_stripping():
    # If the response was truncated mid-reasoning before closing </think>
    truncated = "<think>This was thinking that never got closed"
    assert _strip_chain_of_thought(truncated) == ""

    # Partially closed tag
    mixed = "<think>Thought 1</think>Answer 1 <think>Thought 2 unclosed"
    assert _strip_chain_of_thought(mixed) == "Answer 1"
