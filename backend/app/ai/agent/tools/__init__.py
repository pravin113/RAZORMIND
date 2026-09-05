from __future__ import annotations

from app.ai.agent.tools.base import ToolDefinition, ToolRegistry
from app.ai.agent.tools.customer_tools import tool_get_customer_history
from app.ai.agent.tools.payment_tools import tool_get_payment_details
from app.ai.agent.tools.policy_tools import tool_evaluate_recovery_policy, tool_get_policy
from app.ai.agent.tools.rag_tools import tool_search_merchant_knowledge
from app.ai.agent.tools.recovery_tools import (
    tool_execute_recovery_workflow,
    tool_get_recovery_probability,
    tool_get_recovery_summary,
)
from app.ai.agent.tools.revenue_tools import tool_get_failed_payments, tool_get_revenue_metrics
from app.ai.agent.tools.risk_tools import tool_get_risk_score, tool_get_risk_summary
from app.ai.agent.tools.transaction_tools import tool_get_transaction

ALL_TOOLS: list[ToolDefinition] = [
    tool_get_transaction,
    tool_get_customer_history,
    tool_get_risk_score,
    tool_get_recovery_probability,
    tool_get_revenue_metrics,
    tool_get_failed_payments,
    tool_get_risk_summary,
    tool_get_recovery_summary,
    tool_get_payment_details,
    tool_get_policy,
    tool_evaluate_recovery_policy,
    tool_execute_recovery_workflow,
    tool_search_merchant_knowledge,
]


def get_default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for tool in ALL_TOOLS:
        registry.register(tool)
    return registry


__all__ = [
    "ALL_TOOLS",
    "ToolDefinition",
    "ToolRegistry",
    "get_default_tool_registry",
    "tool_get_customer_history",
    "tool_get_failed_payments",
    "tool_get_payment_details",
    "tool_get_policy",
    "tool_evaluate_recovery_policy",
    "tool_execute_recovery_workflow",
    "tool_search_merchant_knowledge",
    "tool_get_recovery_probability",
    "tool_get_recovery_summary",
    "tool_get_revenue_metrics",
    "tool_get_risk_score",
    "tool_get_risk_summary",
    "tool_get_transaction",
]

