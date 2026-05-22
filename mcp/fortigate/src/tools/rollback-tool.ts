import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { FortiOSClient } from "../client/fortios-client.js";
import { globalBackupManager } from "../backup/manager.js";

export const ROLLBACK_TOOL_NAME = "fortios_rollback";

/**
 * Rollback tool definition
 */
export function getRollbackTool(): Tool {
  return {
    name: ROLLBACK_TOOL_NAME,
    description:
      "Rollback the last configuration change. " +
      "Restores the previous state before the most recent create/update/delete operation.",
    inputSchema: {
      type: "object",
      properties: {
        confirm: {
          type: "boolean",
          description: "Set to true to confirm rollback",
        },
      },
      required: ["confirm"],
    } as Tool["inputSchema"],
  };
}

/**
 * Handle rollback operation
 */
export async function handleRollback(
  args: Record<string, unknown>,
  client: FortiOSClient,
  dryRun: boolean
): Promise<unknown> {
  const confirm = args.confirm === true;
  if (!confirm) {
    return {
      status: "cancelled",
      message: "Rollback not confirmed. Set confirm: true to proceed.",
    };
  }

  if (!globalBackupManager.hasBackup()) {
    return {
      status: "no_backup",
      message: "No backup available. Rollback can only be performed after a create/update/delete operation.",
    };
  }

  const backup = globalBackupManager.getLast();
  if (!backup) {
    return {
      status: "error",
      message: "Failed to retrieve backup.",
    };
  }

  if (dryRun) {
    return {
      dryRun: true,
      operation: "rollback",
      backup: {
        path: backup.path,
        operation: backup.operation,
        timestamp: backup.timestamp,
      },
      message: "Would restore configuration to previous state",
    };
  }

  // Restore: PUT the old data back
  try {
    const result = await client.put(backup.path, { data: backup.data });
    globalBackupManager.pop(); // Remove used backup
    return {
      status: "success",
      message: `Rolled back ${backup.operation} on ${backup.path}`,
      result,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      status: "error",
      message: `Rollback failed: ${message}`,
    };
  }
}
