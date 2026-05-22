import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { FortiOSClient } from "../client/fortios-client.js";

export const BULK_CREATE_TOOL_NAME = "fortios_bulk_create";
export const BULK_DELETE_TOOL_NAME = "fortios_bulk_delete";

function toolToPath(toolName: string): string {
  const parts = toolName.replace("fortios_", "").split("_");
  const moduleName = parts[0];
  const resource = parts.slice(1).join("_");
  return `/${moduleName}/${resource}`;
}

export function getBulkCreateTool(): Tool {
  return {
    name: BULK_CREATE_TOOL_NAME,
    description:
      "Create multiple FortiOS objects in a single operation. " +
      "Provides per-item success/failure reporting.",
    inputSchema: {
      type: "object",
      properties: {
        tool: {
          type: "string",
          description: "Target tool name (e.g., fortios_firewall_address)",
        },
        items: {
          type: "array",
          items: { type: "object" },
          description: "Array of objects to create",
        },
      },
      required: ["tool", "items"],
    } as Tool["inputSchema"],
  };
}

export function getBulkDeleteTool(): Tool {
  return {
    name: BULK_DELETE_TOOL_NAME,
    description:
      "Delete multiple FortiOS objects in a single operation. " +
      "Provides per-item success/failure reporting.",
    inputSchema: {
      type: "object",
      properties: {
        tool: {
          type: "string",
          description: "Target tool name (e.g., fortios_firewall_address)",
        },
        ids: {
          type: "array",
          items: { type: "string" },
          description: "Array of IDs or names to delete",
        },
      },
      required: ["tool", "ids"],
    } as Tool["inputSchema"],
  };
}

export async function handleBulkCreate(
  args: Record<string, unknown>,
  client: FortiOSClient,
  dryRun: boolean
): Promise<unknown> {
  const toolName = args.tool as string;
  const items = args.items as Array<Record<string, unknown>>;
  const path = toolToPath(toolName);

  const results = [];
  let success = 0;
  let failed = 0;

  for (const item of items) {
    if (dryRun) {
      results.push({ status: "dry_run", name: item.name || "(unnamed)", path });
      success++;
      continue;
    }

    try {
      const result = await client.post(path, { data: item });
      results.push({ status: "success", name: item.name || "(unnamed)", result });
      success++;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      results.push({ status: "error", name: item.name || "(unnamed)", error: message });
      failed++;
    }
  }

  return {
    status: "complete",
    path,
    total: items.length,
    success,
    failed,
    results,
  };
}

export async function handleBulkDelete(
  args: Record<string, unknown>,
  client: FortiOSClient,
  dryRun: boolean
): Promise<unknown> {
  const toolName = args.tool as string;
  const ids = args.ids as string[];
  const path = toolToPath(toolName);

  const results = [];
  let success = 0;
  let failed = 0;

  for (const id of ids) {
    if (dryRun) {
      results.push({ status: "dry_run", id, path: `${path}/${id}` });
      success++;
      continue;
    }

    try {
      const result = await client.delete(`${path}/${encodeURIComponent(id)}`);
      results.push({ status: "success", id, result });
      success++;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      results.push({ status: "error", id, error: message });
      failed++;
    }
  }

  return {
    status: "complete",
    path,
    total: ids.length,
    success,
    failed,
    results,
  };
}
