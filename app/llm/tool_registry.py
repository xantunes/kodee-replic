"""Tool registry for managing callable tools."""

import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from app.services.tool_logger import log_tool_execution


class ToolRegistry:
    """Registry for tools that can be called by the LLM."""

    def __init__(self) -> None:
        """Initialize the tool registry with default tools."""
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Callable[..., str]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register the built-in example tools."""
        self.register_tool(
            name="get_weather",
            description="Get the current weather for a given location.",
            handler_fn=self._get_weather,
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city or location to get weather for.",
                    }
                },
                "required": ["location"],
            },
        )
        self.register_tool(
            name="calculate",
            description="Evaluate a mathematical expression and return the result.",
            handler_fn=self._calculate,
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A mathematical expression to evaluate, e.g. '2 + 2'.",
                    }
                },
                "required": ["expression"],
            },
        )
        self.register_tool(
            name="get_time",
            description="Get the current date and time.",
            handler_fn=self._get_time,
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

    @staticmethod
    def _get_weather(location: str) -> str:
        """Return dummy weather data."""
        return f"The weather in {location} is sunny with a temperature of 25°C."

    @staticmethod
    def _calculate(expression: str) -> str:
        """Safely evaluate a mathematical expression."""
        try:
            allowed_names = {
                "abs": abs,
                "max": max,
                "min": min,
                "pow": pow,
                "round": round,
            }
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return str(result)
        except Exception as e:
            return f"Error evaluating expression: {e}"

    @staticmethod
    def _get_time() -> str:
        """Return the current date and time."""
        return datetime.now().isoformat()

    def register_tool(
        self,
        name: str,
        description: str,
        handler_fn: Callable[..., str],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a new tool.

        Args:
            name: Unique name for the tool.
            description: Description of what the tool does.
            handler_fn: Callable function that executes the tool.
            parameters: JSON Schema for the tool parameters.
        """
        self._handlers[name] = handler_fn
        self._tools[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters or {"type": "object", "properties": {}, "required": []},
            },
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return all registered tools in OpenAI function format.

        Returns:
            List of tool definitions.
        """
        return list(self._tools.values())

    def execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Execute a registered tool with the given arguments.

        Args:
            name: Name of the tool to execute.
            args: Arguments to pass to the tool handler.

        Returns:
            Result of the tool execution as a string.
        """
        if name not in self._handlers:
            log_tool_execution(
                tool_name=name,
                arguments=args,
                result=f"Error: Tool '{name}' not found.",
                success=False,
                duration_ms=0,
            )
            return f"Error: Tool '{name}' not found."
        handler = self._handlers[name]
        start = time.time()
        try:
            result = handler(**args)
            success = True
        except Exception as e:
            result = f"Error executing tool '{name}': {e}"
            success = False
        duration_ms = int((time.time() - start) * 1000)
        log_tool_execution(
            tool_name=name,
            arguments=args,
            result=result,
            success=success,
            duration_ms=duration_ms,
        )
        return result
