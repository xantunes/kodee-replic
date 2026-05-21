"""Tests for MCP server and client."""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.mcp.client import MCPClient
from app.mcp.tools.backup_tools import create_backup, list_backups, restore_backup
from app.mcp.tools.dns_tools import create_dns_record, delete_dns_record, list_dns_records
from app.mcp.tools.monitoring_tools import check_server_health, get_server_metrics, get_website_status
from app.mcp.tools.user_tools import get_user_info, list_user_sites


class TestMCPServerTools:
    """Tests for individual MCP server tool functions."""

    def test_create_dns_record(self) -> None:
        """Test create_dns_record returns stub confirmation."""
        result = create_dns_record("example.com", "www", "A", "192.0.2.1", ttl=300)
        assert "DNS record created" in result
        assert "www.example.com" in result
        assert "A" in result
        assert "192.0.2.1" in result
        assert "TTL: 300" in result

    def test_list_dns_records(self) -> None:
        """Test list_dns_records returns stub records."""
        result = list_dns_records("example.com")
        assert "DNS records for example.com" in result
        assert "192.0.2.1" in result
        assert "CNAME" in result
        assert "MX" in result

    def test_delete_dns_record(self) -> None:
        """Test delete_dns_record returns stub confirmation."""
        result = delete_dns_record("example.com", "www", "A")
        assert "DNS record deleted" in result
        assert "www.example.com" in result
        assert "A" in result

    def test_create_backup(self) -> None:
        """Test create_backup returns stub confirmation with backup ID."""
        result = create_backup("site-123", label="daily")
        assert "Backup created for site site-123" in result
        assert "bak-" in result
        assert "daily" in result

    def test_restore_backup(self) -> None:
        """Test restore_backup returns stub confirmation."""
        result = restore_backup("bak-abc123", "site-123")
        assert "Restoring site site-123 from backup bak-abc123" in result

    def test_list_backups(self) -> None:
        """Test list_backups returns stub list."""
        result = list_backups("site-123")
        assert "Backups for site site-123" in result
        assert "bak-" in result

    def test_check_server_health(self) -> None:
        """Test check_server_health returns stub health report."""
        result = check_server_health("srv-001")
        assert "srv-001" in result
        assert "HEALTHY" in result
        assert "Uptime" in result

    def test_get_website_status(self) -> None:
        """Test get_website_status returns stub status."""
        result = get_website_status("https://example.com")
        assert "https://example.com" in result
        assert "UP" in result
        assert "200" in result

    def test_get_server_metrics(self) -> None:
        """Test get_server_metrics returns stub metrics."""
        result = get_server_metrics("srv-001", metric="cpu")
        assert "srv-001" in result
        assert "cpu" in result
        assert "42%" in result

    def test_get_user_info(self) -> None:
        """Test get_user_info returns stub user details."""
        result = get_user_info("user-001")
        assert "user-001" in result
        assert "Demo User" in result
        assert "Active" in result

    def test_list_user_sites(self) -> None:
        """Test list_user_sites returns stub site list."""
        result = list_user_sites("user-001")
        assert "Sites for user user-001" in result
        assert "site-001" in result
        assert "example.com" in result


class TestMCPClient:
    """Tests for MCPClient."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools(self) -> None:
        """Test that list_tools returns available tools."""
        client = MCPClient()
        tools = await client.list_tools()
        assert isinstance(tools, list)
        assert len(tools) >= 8
        tool_names = {t["function"]["name"] for t in tools}
        assert "create_dns_record" in tool_names
        assert "list_dns_records" in tool_names
        assert "create_backup" in tool_names
        assert "check_server_health" in tool_names
        assert "get_user_info" in tool_names

    @pytest.mark.asyncio
    async def test_call_tool_executes_correctly(self) -> None:
        """Test that call_tool executes a tool and returns result."""
        client = MCPClient()
        result = await client.call_tool(
            "create_dns_record",
            {"zone": "example.com", "name": "www", "type": "A", "value": "192.0.2.1"},
        )
        assert "DNS record created" in result

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self) -> None:
        """Test that call_tool handles unknown tools gracefully."""
        client = MCPClient()
        result = await client.call_tool("nonexistent_tool", {})
        assert "Error" in result
