"""FastMCP server for Kodee Replica.

Imports and registers all domain-specific tools from app.mcp.tools modules.
"""

# Import the mcp instance and all tool modules so decorators register tools.
from app.mcp.tools import mcp  # noqa: F401
from app.mcp.tools import backup_tools  # noqa: F401
from app.mcp.tools import dns_tools  # noqa: F401
from app.mcp.tools import monitoring_tools  # noqa: F401
from app.mcp.tools import user_tools  # noqa: F401

if __name__ == "__main__":
    mcp.run()
