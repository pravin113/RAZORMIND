from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

import httpx
from sqlalchemy.orm import Session

from app.ai.agent.config import AgentConfig, get_agent_config
from app.ai.agent.prompts import RAZORMIND_SYSTEM_PROMPT
from app.ai.agent.tools import ToolRegistry, get_default_tool_registry

logger = logging.getLogger(__name__)


class AgentServiceUnavailableError(RuntimeError):
    """Raised when the LLM service is disabled or unreachable."""
    pass


class AgentProcessingError(RuntimeError):
    """Raised when an internal error occurs during agent execution."""
    pass


@dataclass
class AgentResult:
    answer: str
    tools_used: list[str]
    model: str
    session_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _parse_tool_arguments(raw_args: Any) -> dict[str, Any]:
    """Safely parse tool arguments whether provided as a JSON string, dict, or empty."""
    if isinstance(raw_args, dict):
        return raw_args
    if isinstance(raw_args, str):
        cleaned = raw_args.strip()
        if not cleaned:
            return {}
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
            return {"value": parsed}
        except json.JSONDecodeError as exc:
            logger.warning("Failed to decode tool arguments JSON: %s (error: %s)", raw_args, exc)
            return {}
    return {}


def _strip_chain_of_thought(text: str) -> str:
    """Strip out any internal <think>...</think> reasoning tags, including unclosed tags."""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()


class RazorMindAgent:
    def __init__(
        self,
        config: AgentConfig | None = None,
        tool_registry: ToolRegistry | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.config = config or get_agent_config()
        self.tool_registry = tool_registry or get_default_tool_registry()
        self._custom_client = http_client
        self._sessions: dict[str, list[dict[str, Any]]] = {}

    def _get_client(self) -> httpx.Client:
        if self._custom_client is not None:
            return self._custom_client
        return httpx.Client(timeout=self.config.timeout_seconds)

    def get_session_history(self, session_id: str) -> list[dict[str, Any]]:
        return self._sessions.setdefault(session_id, [])

    def chat(
        self,
        message: str,
        db: Session,
        merchant_id: UUID | None = None,
        session_id: str | None = None,
    ) -> AgentResult:
        if not self.config.enabled:
            raise AgentServiceUnavailableError("Qwen AI agent is currently disabled in configuration.")

        active_session_id = session_id or str(uuid4())
        session_messages = self.get_session_history(active_session_id)

        # Context scope note if merchant_id provided
        merchant_context = f"\nActive Merchant ID context: {merchant_id}" if merchant_id else ""
        system_content = RAZORMIND_SYSTEM_PROMPT + merchant_context

        conversation: list[dict[str, Any]] = [{"role": "system", "content": system_content}]
        conversation.extend(session_messages[-10:])  # keep last 10 messages for lightweight context
        conversation.append({"role": "user", "content": message})

        tools_spec = self.tool_registry.to_openai_tools()
        tools_used: list[str] = []
        final_answer = ""
        max_turns = 5

        client = self._get_client()

        try:
            for turn in range(max_turns):
                payload = {
                    "model": self.config.model_name,
                    "messages": conversation,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                }
                if tools_spec:
                    payload["tools"] = tools_spec
                    payload["tool_choice"] = "auto"

                try:
                    response = client.post(
                        f"{self.config.base_url.rstrip('/')}/chat/completions",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )
                except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
                    logger.warning("Failed to connect to Qwen inference server: %s", exc)
                    raise AgentServiceUnavailableError(
                        f"Qwen inference server unreachable at {self.config.base_url}."
                    ) from exc

                if response.status_code != 200:
                    logger.error("LLM inference error %s: %s", response.status_code, response.text)
                    raise AgentServiceUnavailableError(
                        f"Qwen inference returned status {response.status_code}: {response.text[:200]}"
                    )

                data = response.json()
                choice = data.get("choices", [{}])[0]
                assistant_msg = choice.get("message", {})
                content = assistant_msg.get("content") or ""
                tool_calls = assistant_msg.get("tool_calls")

                # Handle tool calls
                if tool_calls:
                    clean_tool_calls = []
                    tool_results_to_append = []

                    for tc in tool_calls:
                        tc_id = tc.get("id") or f"call_{uuid4().hex[:8]}"
                        fn = tc.get("function", {})
                        tool_name = fn.get("name")
                        raw_args = fn.get("arguments", "{}")

                        # Safely parse arguments whether JSON string or dict
                        parsed_args = _parse_tool_arguments(raw_args)
                        # Ensure raw_args is formatted as a JSON string for OpenAI API message continuation
                        args_str = raw_args if isinstance(raw_args, str) else json.dumps(raw_args)

                        clean_tool_calls.append({
                            "id": tc_id,
                            "type": tc.get("type", "function"),
                            "function": {
                                "name": tool_name,
                                "arguments": args_str,
                            },
                        })

                        if tool_name not in tools_used:
                            tools_used.append(tool_name)

                        logger.info("Agent invoking tool: %s with args: %s", tool_name, parsed_args)
                        result = self.tool_registry.execute(tool_name, db=db, arguments=parsed_args)

                        tool_results_to_append.append({
                            "role": "tool",
                            "tool_call_id": tc_id,
                            "name": tool_name,
                            "content": json.dumps(result),
                        })

                    # Append clean assistant message with standardized tool_calls array
                    conversation.append({
                        "role": "assistant",
                        "content": assistant_msg.get("content") or "",
                        "tool_calls": clean_tool_calls,
                    })
                    # Append matching tool result messages
                    conversation.extend(tool_results_to_append)
                    continue

                # No tool calls: final answer produced
                final_answer = _strip_chain_of_thought(content)
                if not final_answer and tools_used:
                    final_answer = "Analysis completed based on the retrieved merchant metrics."
                break

        except AgentServiceUnavailableError:
            raise
        except Exception as exc:
            logger.exception("Agent reasoning loop encountered an error: %s", exc)
            raise AgentProcessingError(f"Agent reasoning failed: {str(exc)}") from exc

        if not final_answer:
            final_answer = "I was unable to retrieve a complete answer for your request."

        # Update session memory
        session_messages.append({"role": "user", "content": message})
        session_messages.append({"role": "assistant", "content": final_answer})

        return AgentResult(
            answer=final_answer,
            tools_used=tools_used,
            model=self.config.model_name,
            session_id=active_session_id,
            metadata={"turns": turn + 1},
        )



_agent_instance: RazorMindAgent | None = None


def get_razormind_agent() -> RazorMindAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = RazorMindAgent()
    return _agent_instance
