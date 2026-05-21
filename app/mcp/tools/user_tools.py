"""User management tools for the MCP server."""

from app.mcp.tools import mcp


@mcp.tool()
def get_user_info(user_id: str) -> str:
    """Get information about a user.

    Args:
        user_id: The user identifier.

    Returns:
        User information.
    """
    return (
        f"User info for {user_id}:\n"
        f"- Name: Demo User\n"
        f"- Email: demo@example.com\n"
        f"- Role: Administrator\n"
        f"- Status: Active"
    )


@mcp.tool()
def list_user_sites(user_id: str) -> str:
    """List all sites owned by a user.

    Args:
        user_id: The user identifier.

    Returns:
        Formatted list of sites.
    """
    return (
        f"Sites for user {user_id}:\n"
        f"1. site-001 - example.com (Active)\n"
        f"2. site-002 - blog.example.com (Active)\n"
        f"3. site-003 - shop.example.com (Maintenance)"
    )
