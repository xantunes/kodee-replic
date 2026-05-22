"""MCP client for multiple FortiGate servers (stdio-based)."""

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


# ─── Firewall Configuration Registry ───────────────────────────

_FIREWALL_CONFIGS = [
    {
        "name": "internet",
        "label": "Firewall Internet",
        "host": settings.FORTIOS_INTERNET_HOST,
        "token": settings.FORTIOS_INTERNET_API_TOKEN,
        "verify_ssl": settings.FORTIOS_INTERNET_VERIFY_SSL,
        "readonly": settings.FORTIOS_INTERNET_READONLY,
    },
    {
        "name": "datacenter",
        "label": "Firewall Datacenter",
        "host": settings.FORTIOS_DATACENTER_HOST,
        "token": settings.FORTIOS_DATACENTER_API_TOKEN,
        "verify_ssl": settings.FORTIOS_DATACENTER_VERIFY_SSL,
        "readonly": settings.FORTIOS_DATACENTER_READONLY,
    },
    {
        "name": "vpn",
        "label": "Firewall VPN",
        "host": settings.FORTIOS_VPN_HOST,
        "token": settings.FORTIOS_VPN_API_TOKEN,
        "verify_ssl": settings.FORTIOS_VPN_VERIFY_SSL,
        "readonly": settings.FORTIOS_VPN_READONLY,
    },
    {
        "name": "interna",
        "label": "Firewall Rede Interna",
        "host": settings.FORTIOS_INTERNA_HOST,
        "token": settings.FORTIOS_INTERNA_API_TOKEN,
        "verify_ssl": settings.FORTIOS_INTERNA_VERIFY_SSL,
        "readonly": settings.FORTIOS_INTERNA_READONLY,
    },
]


def _get_enabled_firewalls() -> List[Dict[str, Any]]:
    """Return only firewalls that have host configured."""
    return [fw for fw in _FIREWALL_CONFIGS if fw["host"]]


class FortigateMCPClient:
    """Client for interacting with a single FortiGate MCP server via stdio."""

    def __init__(self, fw_config: Dict[str, Any]) -> None:
        """Initialize the FortiGate MCP client for a specific firewall.

        Args:
            fw_config: Firewall configuration dict with host, token, etc.
        """
        self.fw_name = fw_config["name"]
        self.fw_label = fw_config["label"]
        self.fw_config = fw_config
        self._session = None
        self._tools_cache: Optional[List[Dict[str, Any]]] = None

    async def _ensure_session(self):
        """Ensure MCP session is initialized."""
        if self._session is not None:
            return

        sdk = _get_mcp_sdk()
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "mcp", "fortigate")
        dist_path = os.path.join(os.path.abspath(base_dir), "dist", "index.js")

        if not os.path.exists(dist_path):
            raise RuntimeError(f"FortiGate MCP server not found at {dist_path}")

        server_params = StdioServerParameters(
            command="node",
            args=[dist_path],
            env={
                **os.environ,
                "FORTIOS_HOST": self.fw_config["host"],
                "FORTIOS_API_TOKEN": self.fw_config["token"],
                "FORTIOS_VERIFY_SSL": "false" if not self.fw_config["verify_ssl"] else "true",
                "FORTIOS_READONLY": "true" if self.fw_config["readonly"] else "false",
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

        # Prefix tool names with firewall name to avoid collisions
        self._tools_cache = [
            {
                "type": "function",
                "function": {
                    "name": f"{self.fw_name}_{tool.name}",
                    "description": f"[{self.fw_label}] {tool.description or ''}",
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tools_result.tools
        ]
        return self._tools_cache

    async def call_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Call a tool on the FortiGate MCP server.

        Args:
            name: Name of the tool to call (with firewall prefix).
            args: Arguments to pass to the tool.

        Returns:
            Result of the tool execution as a string.
        """
        import time

        await self._ensure_session()

        # Strip firewall prefix to get the actual tool name
        actual_name = name
        prefix = f"{self.fw_name}_"
        if actual_name.startswith(prefix):
            actual_name = actual_name[len(prefix):]

        start = time.time()
        try:
            result = await self._session.call_tool(actual_name, args)
            texts = []
            for content in result.content:
                if hasattr(content, "text"):
                    texts.append(content.text)
                elif isinstance(content, dict):
                    texts.append(content.get("text", json.dumps(content)))
                else:
                    texts.append(str(content))
            output = f"[{self.fw_label}]\n" + "\n".join(texts)
            success = True
        except Exception as e:
            output = f"[{self.fw_label}] Error calling tool '{actual_name}': {e}"
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

    async def health_check(self) -> str:
        """Run a quick health check on this firewall."""
        try:
            return await self.call_tool(f"{self.fw_name}_fortios_health_check", {})
        except Exception as e:
            return f"[{self.fw_label}] Health check failed: {e}"

    async def close(self):
        """Close the MCP session."""
        if self._session is not None:
            await self._session.__aexit__(None, None, None)
            self._session = None
            self._tools_cache = None


class FortigateClientPool:
    """Pool of FortiGate MCP clients — one per configured firewall."""

    def __init__(self) -> None:
        """Initialize clients for all configured firewalls."""
        self.clients: Dict[str, FortigateMCPClient] = {}
        for fw in _get_enabled_firewalls():
            self.clients[fw["name"]] = FortigateMCPClient(fw)

    def get_client(self, name: str) -> Optional[FortigateMCPClient]:
        """Get a specific firewall client by name."""
        return self.clients.get(name)

    def list_firewalls(self) -> List[str]:
        """List names of configured firewalls."""
        return list(self.clients.keys())

    async def list_all_tools(self) -> List[Dict[str, Any]]:
        """List tools from all configured firewalls."""
        all_tools: List[Dict[str, Any]] = []
        for client in self.clients.values():
            try:
                tools = await client.list_tools()
                all_tools.extend(tools)
            except Exception as e:
                # Gracefully skip unreachable firewalls
                all_tools.append({
                    "type": "function",
                    "function": {
                        "name": f"{client.fw_name}_unavailable",
                        "description": f"[{client.fw_label}] Firewall unreachable: {e}",
                        "parameters": {"type": "object", "properties": {}},
                    },
                })
        return all_tools

    async def call_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Call a tool, routing to the correct firewall based on prefix."""
        for fw_name, client in self.clients.items():
            if name.startswith(f"{fw_name}_"):
                return await client.call_tool(name, args)
        return f"Error: No firewall client found for tool '{name}'"

    async def health_check_all(self) -> Dict[str, str]:
        """Run health checks on all firewalls."""
        results = {}
        for fw_name, client in self.clients.items():
            results[fw_name] = await client.health_check()
        return results

    async def close_all(self):
        """Close all MCP sessions."""
        for client in self.clients.values():
            await client.close()
