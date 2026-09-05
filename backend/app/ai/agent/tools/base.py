from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    func: Callable[..., dict[str, Any]]

    def to_openai_dict(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            logger.warning("Overwriting existing tool registration: %s", tool.name)
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_names(self) -> list[str]:
        return list(self._tools.keys())

    def to_openai_tools(self) -> list[dict[str, Any]]:
        return [tool.to_openai_dict() for tool in self._tools.values()]

    def execute(self, name: str, db: Session, arguments: dict[str, Any] | str | None = None) -> dict[str, Any]:
        tool = self.get(name)
        if tool is None:
            return {"error": f"Tool '{name}' not found in registry."}

        args: dict[str, Any] = {}
        if isinstance(arguments, str):
            try:
                args = json.loads(arguments) if arguments.strip() else {}
            except json.JSONDecodeError as exc:
                return {"error": f"Invalid JSON arguments for tool '{name}': {exc}"}
        elif isinstance(arguments, dict):
            args = arguments

        try:
            return tool.func(db=db, **args)
        except TypeError as exc:
            logger.warning("Tool %s parameter error: %s", name, exc)
            return {"error": f"Parameter validation error for tool '{name}': {exc}"}
        except Exception as exc:
            logger.exception("Error executing tool %s: %s", name, exc)
            return {"error": f"Error executing tool '{name}': {str(exc)}"}
