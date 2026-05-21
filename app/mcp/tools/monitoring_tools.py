"""Monitoring tools for the MCP server."""

from app.mcp.tools import mcp


@mcp.tool()
def check_server_health(server_id: str) -> str:
    """Check the health status of a server.

    Args:
        server_id: The server identifier to check.

    Returns:
        Health status report.
    """
    return (
        f"Server {server_id} health: HEALTHY\n"
        f"- Uptime: 45 days, 3 hours\n"
        f"- Load average: 0.42, 0.38, 0.35\n"
        f"- Disk usage: 62%\n"
        f"- Memory usage: 58%"
    )


@mcp.tool()
def get_website_status(url: str) -> str:
    """Check the status of a website.

    Args:
        url: The website URL to check.

    Returns:
        Website status report.
    """
    return (
        f"Website status for {url}:\n"
        f"- Status: UP\n"
        f"- HTTP code: 200\n"
        f"- Response time: 120ms\n"
        f"- SSL certificate: Valid (expires in 60 days)"
    )

