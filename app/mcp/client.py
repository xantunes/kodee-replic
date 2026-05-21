"""MCP client for interacting with the Kodee MCP server."""

from typing import Any, Dict, List

# Import tool modules to ensure tool registration happens before client use
from app.mcp.tools import mcp
from app.mcp.tools import backup_tools, dns_tools, monitoring_tools, user_tools  # noqa: F401


class MCPClient:
    """Client for interacting with the in-process MCP server."""

    def __init__(self) -> None:
        """Initialize the MCP client."""
        self._mcp = mcp

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server.

        Returns:
            List of tool definitions in OpenAI function format.
        """
        tools = await self._mcp.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in tools
        ]

    async def call_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Call a tool on the MCP server.

        Args:
            name: Name of the tool to call.
            args: Arguments to pass to the tool.

        Returns:
            Result of the tool execution as a string.
        """
        try:
            result = await self._mcp.call_tool(name, args)
            texts = [content.text for content in result.content]
            return "\n".join(texts)
        except Exception as e:
            return f"Error calling MCP tool '{name}': {e}"
