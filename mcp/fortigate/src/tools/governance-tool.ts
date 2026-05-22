import { Tool } from "@modelcontextprotocol/sdk/types.js";
import {
  freeze,
  unfreeze,
  isFrozen,
  getFreezeStatus,
  approveChange,
  listPendingChanges,
  isReadonly,
} from "../governance/access-control.js";

export const FREEZE_TOOL_NAME = "fortios_freeze";
export const UNFREEZE_TOOL_NAME = "fortios_unfreeze";
export const FREEZE_STATUS_TOOL_NAME = "fortios_freeze_status";
export const PENDING_CHANGES_TOOL_NAME = "fortios_pending_changes";
export const APPROVE_CHANGE_TOOL_NAME = "fortios_approve_change";
export const GOVERNANCE_STATUS_TOOL_NAME = "fortios_governance_status";

export function getFreezeTool(): Tool {
  return {
    name: FREEZE_TOOL_NAME,
    description:
      "EMERGENCY: Immediately freeze all configuration changes. " +
      "Requires operator or approver token.",
    inputSchema: {
      type: "object",
      properties: {
        reason: { type: "string", description: "Reason for freeze (required)" },
        operator_token: { type: "string", description: "Operator/Approver token" },
      },
      required: ["reason", "operator_token"],
    } as Tool["inputSchema"],
  };
}

export function getUnfreezeTool(): Tool {
  return {
    name: UNFREEZE_TOOL_NAME,
    description: "Unfreeze the system. Requires emergency token.",
    inputSchema: {
      type: "object",
      properties: {
        emergency_token: { type: "string", description: "Emergency token" },
      },
      required: ["emergency_token"],
    } as Tool["inputSchema"],
  };
}

export function getFreezeStatusTool(): Tool {
  return {
    name: FREEZE_STATUS_TOOL_NAME,
    description: "Check if the system is frozen and by whom.",
    inputSchema: { type: "object", properties: {} } as Tool["inputSchema"],
  };
}

export function getPendingChangesTool(): Tool {
  return {
    name: PENDING_CHANGES_TOOL_NAME,
    description: "List all pending changes awaiting approval (Two-Person Rule).",
    inputSchema: { type: "object", properties: {} } as Tool["inputSchema"],
  };
}

export function getApproveChangeTool(): Tool {
  return {
    name: APPROVE_CHANGE_TOOL_NAME,
    description: "Approve a pending change. Requires approver token.",
    inputSchema: {
      type: "object",
      properties: {
        change_id: { type: "string", description: "Change ID to approve" },
        approver_token: { type: "string", description: "Approver token" },
      },
      required: ["change_id", "approver_token"],
    } as Tool["inputSchema"],
  };
}

export function getGovernanceStatusTool(): Tool {
  return {
    name: GOVERNANCE_STATUS_TOOL_NAME,
    description: "Show current governance configuration: readonly, freeze, change windows.",
    inputSchema: { type: "object", properties: {} } as Tool["inputSchema"],
  };
}

export async function handleFreeze(args: Record<string, unknown>): Promise<unknown> {
  const reason = args.reason as string;
  const token = args.operator_token as string;
  freeze(reason, token);
  return { status: "frozen", reason, since: new Date().toISOString() };
}

export async function handleUnfreeze(args: Record<string, unknown>): Promise<unknown> {
  const token = args.emergency_token as string;
  unfreeze(token);
  return { status: "unfrozen", at: new Date().toISOString() };
}

export async function handleFreezeStatus(): Promise<unknown> {
  return { status: "success", ...getFreezeStatus() };
}

export async function handlePendingChanges(): Promise<unknown> {
  const changes = listPendingChanges();
  return {
    status: "success",
    count: changes.length,
    changes: changes.map((c) => ({
      id: c.id,
      tool: c.tool,
      timestamp: c.timestamp,
      expires_at: new Date(c.expires_at).toISOString(),
    })),
  };
}

export async function handleApproveChange(args: Record<string, unknown>): Promise<unknown> {
  const changeId = args.change_id as string;
  const token = args.approver_token as string;
  const change = approveChange(changeId, token);
  return {
    status: "approved",
    change_id: changeId,
    tool: change?.tool,
    message: "Change approved and ready for execution.",
  };
}

export async function handleGovernanceStatus(): Promise<unknown> {
  return {
    status: "success",
    readonly: isReadonly(),
    frozen: isFrozen(),
    freeze_status: getFreezeStatus(),
    change_token_required: isReadonly(),
    two_person_rule: process.env.FORTIOS_OPERATOR_TOKEN && process.env.FORTIOS_APPROVER_TOKEN ? "enabled" : "disabled",
    change_window: process.env.FORTIOS_CHANGE_WINDOW || "not configured",
  };
}
