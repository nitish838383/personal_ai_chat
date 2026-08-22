"""
Central Tool Registry.
AI Agent → Tool Registry → Permission Check → Tool → Result
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Dict, List, Optional
from enum import Enum


class RiskLevel(str, Enum):
    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"


@dataclass
class Tool:
    name: str
    description: str
    provider: str
    risk_level: RiskLevel
    handler: Callable[..., Awaitable[Any]]
    input_schema: dict = field(default_factory=dict)
    requires_confirmation: bool = False


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_for_user(self, allowed_providers: List[str] | None = None) -> List[Tool]:
        tools = list(self._tools.values())
        if allowed_providers is not None:
            tools = [t for t in tools if t.provider in allowed_providers or t.provider == "internal"]
        return tools

    def to_openai_tools(self, tools: List[Tool]) -> List[dict]:
        """Convert registered tools to OpenAI function-calling format."""
        result = []
        for t in tools:
            result.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.input_schema or {"type": "object", "properties": {}},
                },
            })
        return result


# Global registry instance
tool_registry = ToolRegistry()


# Example internal tools (memory, tasks)
async def _create_task_tool(user_id, title: str, **kwargs):
    return {"status": "created", "title": title, "note": "Use /api/v1/tasks for full task management"}


async def _search_memory_tool(user_id, query: str, **kwargs):
    return {"status": "ok", "query": query, "note": "Memory search will use embeddings when configured"}


def register_default_tools():
    tool_registry.register(Tool(
        name="create_task",
        description="Create a task for the user",
        provider="internal",
        risk_level=RiskLevel.WRITE,
        handler=_create_task_tool,
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            },
            "required": ["title"],
        },
        requires_confirmation=False,
    ))
    tool_registry.register(Tool(
        name="search_memory",
        description="Search the user's long-term memory",
        provider="internal",
        risk_level=RiskLevel.READ,
        handler=_search_memory_tool,
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    ))


register_default_tools()
