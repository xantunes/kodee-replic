import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { FortiOSClient } from "../client/fortios-client.js";
import { globalBackupManager } from "../backup/manager.js";
import { diffObjects, formatDiff } from "../utils/diff.js";

export const DIFF_TOOL_NAME = "fortios_diff";

export function getDiffTool(): Tool {
  return {
    name: DIFF_TOOL_NAME,
    description:
      "Compare two FortiOS objects or compare an object with its last backup. " +
      "Shows field-by-field differences in markdown format.",
    inputSchema: {
      type: "object",
      properties: {
        tool: {
          type: "string",
          description: "Tool name (e.g., fortios_firewall_policy)",
        },
        id_a: {
          type: "string",
          description: "ID or name of first object",
        },
        id_b: {
          type: "string",
          description: "ID or name of second object (omit to compare with backup)",
        },
      },
      required: ["tool", "id_a"],
    } as Tool["inputSchema"],
  };
}

export async function handleDiff(
  args: Record<string, unknown>,
  client: FortiOSClient
): Promise<unknown> {
  const toolName = args.tool as string;
  const idA = args.id_a as string;
  const idB = args.id_b as string | undefined;

  // Derive API path from tool name: fortios_firewall_policy -> /firewall/policy
  const parts = toolName.replace("fortios_", "").split("_");
  if (parts.length < 2) {
    return { status: "error", message: "Invalid tool name format" };
  }
  const moduleName = parts[0];
  const resource = parts.slice(1).join("_");
  const basePath = `/${moduleName}/${resource}`;

  try {
    let objA: unknown;
    let objB: unknown;

    // Fetch object A
    const pathA = `${basePath}/${encodeURIComponent(idA)}`;
    objA = await client.get(pathA);

    if (idB) {
      // Compare A vs B
      const pathB = `${basePath}/${encodeURIComponent(idB)}`;
      objB = await client.get(pathB);
    } else {
      // Compare A vs last backup
      const backup = globalBackupManager.getLast();
      if (!backup) {
        return { status: "error", message: "No backup available for comparison" };
      }
      objB = backup.data;
    }

    // Extract results if wrapped
    const unwrap = (o: unknown) => {
      const r = o as Record<string, unknown>;
      return r.results ?? r.result ?? r;
    };

    const diffs = diffObjects(unwrap(objA), unwrap(objB));
    const markdown = formatDiff(diffs);

    return {
      status: "success",
      compared: idB ? `${idA} vs ${idB}` : `${idA} vs last backup`,
      differences_count: diffs.length,
      markdown,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { status: "error", message: `Diff failed: ${message}` };
  }
}
