"""Tests for MCP server setup."""

from app.mcp.server import mcp


class TestMCPServer:
    def test_mcp_server_loaded(self) -> None:
        """Test that the MCP server instance is loaded."""
        assert mcp is not None
        assert mcp.name == "kodee-mcp"
