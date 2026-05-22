import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { readAudit } from "../audit/logger.js";

export const AUDIT_TOOL_NAME = "fortios_audit_log";

export function getAuditTool(): Tool {
  return {
    name: AUDIT_TOOL_NAME,
    description:
      "Query the persistent audit log of all operations performed through this MCP server. " +
      "Shows history of changes with timestamps and results.",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Maximum entries to return (default: 50)",
        },
        since: {
          type: "string",
          description: "ISO date to filter from (e.g., 2024-01-01T00:00:00Z)",
        },
        operation: {
          type: "string",
          description: "Filter by operation type: create, update, delete, list, get, search",
        },
      },
    } as Tool["inputSchema"],
  };
}

export async function handleAudit(
  args: Record<string, unknown>
): Promise<unknown> {
  const entries = readAudit({
    limit: (args.limit as number) || 50,
    since: args.since as string | undefined,
    operation: args.operation as string | undefined,
  });

  if (entries.length === 0) {
    return { status: "empty", message: "No audit entries found" };
  }

  return {
    status: "success",
    count: entries.length,
    entries: entries.map((e) => ({
      time: e.timestamp,
      tool: e.tool,
      operation: e.operation,
      status: e.status,
      duration_ms: e.duration_ms,
    })),
  };
}
