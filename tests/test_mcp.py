"""Tests for MCP server and client."""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.mcp.client import MCPClient
from app.mcp.server import (
    calculate,
    create_reminder,
    fetch_url,
    get_system_info,
    get_weather,
    list_directory,
    read_file,
    run_command,
    search_files,
    search_web,
    send_email,
    write_file,
)


class TestMCPServerTools:
    """Tests for individual MCP server tool functions."""

    def test_read_file(self, tmp_path: Any) -> None:
        """Test read_file returns file contents."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        result = read_file(str(test_file))
        assert result == "hello world"

    def test_read_file_not_found(self) -> None:
        """Test read_file returns error for missing file."""
        result = read_file("/nonexistent/file.txt")
        assert "Error" in result

    def test_write_file(self, tmp_path: Any) -> None:
        """Test write_file creates a file."""
        test_file = tmp_path / "output.txt"
        result = write_file(str(test_file), "sample content")
        assert "written successfully" in result
        assert test_file.read_text() == "sample content"

    def test_list_directory(self, tmp_path: Any) -> None:
        """Test list_directory returns entries."""
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        result = list_directory(str(tmp_path))
        assert "a.txt" in result
        assert "b.txt" in result

    def test_search_files(self, tmp_path: Any) -> None:
        """Test search_files finds matching files."""
        (tmp_path / "foo.txt").write_text("")
        (tmp_path / "bar.txt").write_text("")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "foo_log.txt").write_text("")
        result = search_files("foo", str(tmp_path))
        assert "foo.txt" in result
        assert "foo_log.txt" in result
        assert "bar.txt" not in result

    def test_get_system_info(self) -> None:
        """Test get_system_info returns system details."""
        result = get_system_info()
        assert "OS:" in result
        assert "Python:" in result
        assert "Time:" in result

    def test_run_command_safe(self) -> None:
        """Test run_command executes safe commands."""
        result = run_command("echo hello")
        assert "hello" in result

    def test_run_command_blocked(self) -> None:
        """Test run_command blocks dangerous commands."""
        result = run_command("rm -rf /")
        assert "blocked for safety" in result

    @pytest.mark.asyncio
    async def test_fetch_url(self) -> None:
        """Test fetch_url returns content from a URL."""
        mock_response = MagicMock()
        mock_response.text = "<html>Hello</html>"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.mcp.server.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_url("http://example.com")
            assert "<html>Hello</html>" in result

    def test_search_web(self) -> None:
        """Test search_web returns dummy results."""
        result = search_web("python")
        assert "python" in result
        assert "Example result" in result

    def test_calculate(self) -> None:
        """Test calculate evaluates expressions."""
        assert calculate("2 + 3") == "5"
        assert calculate("10 * 5") == "50"

    def test_calculate_error(self) -> None:
        """Test calculate handles invalid expressions."""
        result = calculate("1 / 0")
        assert "Error" in result

    def test_get_weather(self) -> None:
        """Test get_weather returns dummy data."""
        result = get_weather("Lisbon")
        assert "Lisbon" in result
        assert "25°C" in result

    def test_send_email(self) -> None:
        """Test send_email returns stub confirmation."""
        result = send_email("test@example.com", "Hello", "Body text")
        assert "test@example.com" in result
        assert "Hello" in result

    def test_create_reminder(self) -> None:
        """Test create_reminder returns stub confirmation."""
        result = create_reminder("Meeting", "2024-01-01T10:00:00")
        assert "Meeting" in result
        assert "2024-01-01T10:00:00" in result


class TestMCPClient:
    """Tests for MCPClient."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools(self) -> None:
        """Test that list_tools returns available tools."""
        client = MCPClient()
        tools = await client.list_tools()
        assert isinstance(tools, list)
        assert len(tools) >= 10
        tool_names = [t["function"]["name"] for t in tools]
        assert "read_file" in tool_names
        assert "write_file" in tool_names
        assert "calculate" in tool_names

    @pytest.mark.asyncio
    async def test_call_tool_executes_correctly(self) -> None:
        """Test that call_tool executes a tool and returns result."""
        client = MCPClient()
        result = await client.call_tool("calculate", {"expression": "3 * 4"})
        assert result == "12"

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self) -> None:
        """Test that call_tool handles unknown tools gracefully."""
        client = MCPClient()
        result = await client.call_tool("nonexistent_tool", {})
        assert "Error" in result
