from __future__ import annotations

from dataclasses import dataclass
from app.core.config import settings


@dataclass
class AgentConfig:
    enabled: bool = settings.qwen_enabled
    model_path: str = settings.qwen_model_path
    base_url: str = settings.qwen_base_url
    model_name: str = settings.qwen_model_name
    temperature: float = settings.qwen_temperature
    max_tokens: int = settings.qwen_max_tokens
    timeout_seconds: float = settings.qwen_timeout_seconds


def get_agent_config() -> AgentConfig:
    return AgentConfig(
        enabled=settings.qwen_enabled,
        model_path=settings.qwen_model_path,
        base_url=settings.qwen_base_url,
        model_name=settings.qwen_model_name,
        temperature=settings.qwen_temperature,
        max_tokens=settings.qwen_max_tokens,
        timeout_seconds=settings.qwen_timeout_seconds,
    )
