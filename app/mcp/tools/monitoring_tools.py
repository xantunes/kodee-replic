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


@mcp.tool()
def get_server_metrics(server_id: str, metric: str = "cpu") -> str:
    """Get specific metrics for a server.

    Args:
        server_id: The server identifier.
        metric: The metric to retrieve (cpu, memory, disk, network).

    Returns:
        Metric value and details.
    """
    metrics = {
        "cpu": "42% (2.1 GHz average)",
        "memory": "58% (4.6 GB / 8 GB used)",
        "disk": "62% (310 GB / 500 GB used)",
        "network": "1.2 MB/s in, 0.8 MB/s out",
    }
    value = metrics.get(metric.lower(), "Unknown metric")
    return f"Server {server_id} {metric} usage: {value}"
