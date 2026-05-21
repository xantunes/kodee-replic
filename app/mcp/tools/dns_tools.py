"""DNS management tools for the MCP server."""

from app.mcp.tools import mcp


@mcp.tool()
def create_dns_record(zone: str, name: str, type: str, value: str, ttl: int = 3600) -> str:
    """Create a DNS record in the specified zone.

    Args:
        zone: The DNS zone (domain) to create the record in.
        name: The record name (subdomain or @ for root).
        type: The DNS record type (A, AAAA, CNAME, MX, TXT, NS).
        value: The record value.
        ttl: Time-to-live in seconds (default 3600).

    Returns:
        Confirmation message with record details.
    """
    return (
        f"DNS record created: {name}.{zone} {type} -> {value} "
        f"(TTL: {ttl})"
    )


@mcp.tool()
def list_dns_records(zone: str) -> str:
    """List all DNS records in the specified zone.

    Args:
        zone: The DNS zone (domain) to list records for.

    Returns:
        Formatted list of DNS records.
    """
    return (
        f"DNS records for {zone}:\n"
        f"1. @ A 192.0.2.1 (TTL: 3600)\n"
        f"2. www CNAME example.com (TTL: 3600)\n"
        f"3. mail MX 10 mail.example.com (TTL: 3600)"
    )


@mcp.tool()
def delete_dns_record(zone: str, name: str, type: str) -> str:
    """Delete a DNS record from the specified zone.

    Args:
        zone: The DNS zone (domain) to delete the record from.
        name: The record name (subdomain or @ for root).
        type: The DNS record type.

    Returns:
        Confirmation message.
    """
    return f"DNS record deleted: {name}.{zone} {type}"
