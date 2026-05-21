"""MCP client for the FortiGate server (stdio-based)."""

import json
import os
from typing import Any, Dict, List, Optional

from app.config import settings
from app.services.tool_logger import log_tool_execution

# Lazy import to avoid hard dependency at module load time
_mcp_sdk: Optional[Any] = None


def _get_mcp_sdk():
    global _mcp_sdk
    if _mcp_sdk is None:
        import mcp

        _mcp_sdk = mcp
    return _mcp_sdk


class FortigateMCPClient:
    """Client for interacting with the FortiGate MCP server via stdio."""

    def __init__(self) -> None:
        """Initialize the FortiGate MCP client."""
        self._session = None
        self._tools_cache: Optional[List[Dict[str, Any]]] = None

    async def _ensure_session(self):
        """Ensure MCP session is initialized."""
        if self._session is not None:
            return

        sdk = _get_mcp_sdk()
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        # Determine the path to the compiled FortiGate MCP server
        base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "mcp", "fortigate")
        dist_path = os.path.join(os.path.abspath(base_dir), "dist", "index.js")

        if not os.path.exists(dist_path):
            raise RuntimeError(f"FortiGate MCP server not found at {dist_path}")

        server_params = StdioServerParameters(
            command="node",
            args=[dist_path],
            env={
                **os.environ,
                "FORTIOS_HOST": settings.FORTIOS_HOST or "",
                "FORTIOS_API_TOKEN": settings.FORTIOS_API_TOKEN or "",
                "FORTIOS_VERIFY_SSL": "false" if not settings.FORTIOS_VERIFY_SSL else "true",
                "FORTIOS_READONLY": "true" if settings.FORTIOS_READONLY else "false",
            },
        )

        self._read, self._write = await stdio_client(server_params).__aenter__()
        self._session = ClientSession(self._read, self._write)
        await self._session.initialize()

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the FortiGate MCP server.

        Returns:
            List of tool definitions in OpenAI function format.
        """
        if self._tools_cache is not None:
            return self._tools_cache

        await self._ensure_session()
        tools_result = await self._session.list_tools()

        self._tools_cache = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tools_result.tools
        ]
        return self._tools_cache

    async def call_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Call a tool on the FortiGate MCP server.

        Args:
            name: Name of the tool to call.
            args: Arguments to pass to the tool.

        Returns:
            Result of the tool execution as a string.
        """
        import time

        await self._ensure_session()
        start = time.time()
        try:
            result = await self._session.call_tool(name, args)
            texts = []
            for content in result.content:
                if hasattr(content, "text"):
                    texts.append(content.text)
                elif isinstance(content, dict):
                    texts.append(content.get("text", json.dumps(content)))
                else:
                    texts.append(str(content))
            output = "\n".join(texts)
            success = True
        except Exception as e:
            output = f"Error calling FortiGate tool '{name}': {e}"
            success = False
        duration_ms = int((time.time() - start) * 1000)
        log_tool_execution(
            tool_name=name,
            arguments=args,
            result=output,
            success=success,
            duration_ms=duration_ms,
        )
        return output

    async def close(self):
        """Close the MCP session."""
        if self._session is not None:
            await self._session.__aexit__(None, None, None)
            self._session = None
            self._tools_cache = None
