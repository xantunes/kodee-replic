/**
 * Access Control & Governance for Critical Environments
 * Centralizes: readonly mode, two-person rule, emergency freeze, change windows
 */

import { logAudit } from "../audit/logger.js";

// ─── Configuration ──────────────────────────────────────────────

const READONLY = process.env.FORTIOS_READONLY !== "false"; // default true
const CHANGE_TOKEN = process.env.FORTIOS_CHANGE_TOKEN || "";
const OPERATOR_TOKEN = process.env.FORTIOS_OPERATOR_TOKEN || "";
const APPROVER_TOKEN = process.env.FORTIOS_APPROVER_TOKEN || "";
const EMERGENCY_TOKEN = process.env.FORTIOS_EMERGENCY_TOKEN || "";
const CHANGE_WINDOW = process.env.FORTIOS_CHANGE_WINDOW || "";

// ─── State ──────────────────────────────────────────────────────

interface PendingChange {
  id: string;
  tool: string;
  args: Record<string, unknown>;
  operator_hash: string;
  timestamp: string;
  expires_at: number;
}

let frozen = false;
let frozenBy = "";
let frozenAt = "";
const pendingChanges = new Map<string, PendingChange>();

// ─── Readonly Mode ──────────────────────────────────────────────

export function isReadonly(): boolean {
  return READONLY;
}

export function hasChangeToken(token: string): boolean {
  return CHANGE_TOKEN !== "" && token === CHANGE_TOKEN;
}

export function assertCanRead(_toolName: string): void {
  // Read operations are always allowed (unless frozen, checked separately)
  return;
}

export function assertCanMutate(
  _toolName: string,
  changeToken?: string,
  approverToken?: string
): void {
  // 1. Check freeze
  if (frozen) {
    throw new Error(
      `🚫 EMERGENCY FREEZE active since ${frozenAt} by ${frozenBy}. ` +
        `No changes allowed until unfreeze.`
    );
  }

  // 2. Check readonly mode
  if (READONLY) {
    if (!changeToken || !hasChangeToken(changeToken)) {
      throw new Error(
        `🔒 READONLY MODE: This environment requires FORTIOS_CHANGE_TOKEN ` +
          `to perform mutations. Set it or contact your security admin.`
      );
    }
  }

  // 3. Check two-person rule
  if (APPROVER_TOKEN !== "") {
    if (!approverToken || !hasApproverToken(approverToken)) {
      throw new Error(
        `👥 TWO-PERSON RULE: This operation requires an approver token. ` +
          `Ask a colleague to provide FORTIOS_APPROVER_TOKEN.`
      );
    }
  }

  // 4. Check change windows
  const windowError = checkChangeWindow();
  if (windowError) {
    throw new Error(`⏰ ${windowError}`);
  }
}

// ─── Two-Person Rule ────────────────────────────────────────────

export function hasOperatorToken(token: string): boolean {
  return OPERATOR_TOKEN !== "" && token === OPERATOR_TOKEN;
}

export function hasApproverToken(token: string): boolean {
  return APPROVER_TOKEN !== "" && token === APPROVER_TOKEN;
}

export function proposeChange(
  tool: string,
  args: Record<string, unknown>,
  operatorToken: string
): string {
  if (!hasOperatorToken(operatorToken)) {
    throw new Error("Invalid operator token. Cannot propose change.");
  }

  const id = `chg_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
  const now = Date.now();

  pendingChanges.set(id, {
    id,
    tool,
    args,
    operator_hash: hashToken(operatorToken),
    timestamp: new Date().toISOString(),
    expires_at: now + 24 * 60 * 60 * 1000, // 24 hours
  });

  logAudit({
    timestamp: new Date().toISOString(),
    tool: "governance.propose",
    operation: "propose",
    args: { change_id: id, tool },
    status: "success",
    duration_ms: 0,
    token_hash: hashToken(operatorToken),
  });

  return id;
}

export function approveChange(
  changeId: string,
  approverToken: string
): PendingChange | null {
  if (!hasApproverToken(approverToken)) {
    throw new Error("Invalid approver token. Cannot approve change.");
  }

  const change = pendingChanges.get(changeId);
  if (!change) {
    throw new Error(`Change ${changeId} not found or expired.`);
  }

  if (Date.now() > change.expires_at) {
    pendingChanges.delete(changeId);
    throw new Error(`Change ${changeId} has expired.`);
  }

  pendingChanges.delete(changeId);

  logAudit({
    timestamp: new Date().toISOString(),
    tool: "governance.approve",
    operation: "approve",
    args: { change_id: changeId },
    status: "success",
    duration_ms: 0,
    token_hash: hashToken(approverToken),
  });

  return change;
}

export function listPendingChanges(): PendingChange[] {
  const now = Date.now();
  const result: PendingChange[] = [];
  for (const [id, change] of pendingChanges) {
    if (now > change.expires_at) {
      pendingChanges.delete(id);
    } else {
      result.push(change);
    }
  }
  return result;
}

// ─── Emergency Freeze ───────────────────────────────────────────

export function freeze(reason: string, operatorToken: string): void {
  if (!hasOperatorToken(operatorToken) && !hasApproverToken(operatorToken)) {
    throw new Error("Only operator or approver can freeze.");
  }

  frozen = true;
  frozenBy = hashToken(operatorToken);
  frozenAt = new Date().toISOString();

  logAudit({
    timestamp: frozenAt,
    tool: "governance.freeze",
    operation: "freeze",
    args: { reason },
    status: "success",
    duration_ms: 0,
    token_hash: hashToken(operatorToken),
  });
}

export function unfreeze(emergencyToken: string): void {
  if (EMERGENCY_TOKEN === "") {
    throw new Error("FORTIOS_EMERGENCY_TOKEN not configured. Cannot unfreeze.");
  }
  if (emergencyToken !== EMERGENCY_TOKEN) {
    throw new Error("Invalid emergency token.");
  }

  const wasFrozen = frozen;
  frozen = false;
  frozenBy = "";
  frozenAt = "";

  if (wasFrozen) {
    logAudit({
      timestamp: new Date().toISOString(),
      tool: "governance.unfreeze",
      operation: "unfreeze",
      args: {},
      status: "success",
      duration_ms: 0,
      token_hash: hashToken(emergencyToken),
    });
  }
}

export function isFrozen(): boolean {
  return frozen;
}

export function getFreezeStatus(): {
  frozen: boolean;
  since?: string;
  by?: string;
} {
  if (!frozen) return { frozen: false };
  return { frozen: true, since: frozenAt, by: frozenBy };
}

// ─── Change Windows ─────────────────────────────────────────────

interface TimeWindow {
  day: number; // 0=Sun, 1=Mon, ..., 6=Sat
  startMin: number;
  endMin: number;
}

function parseWindows(): TimeWindow[] {
  if (!CHANGE_WINDOW) return []; // No restrictions
  const windows: TimeWindow[] = [];
  const dayMap: Record<string, number> = {
    Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6,
  };

  for (const part of CHANGE_WINDOW.split(",")) {
    const trimmed = part.trim();
    const match = trimmed.match(/^(\w{3})\s+(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$/);
    if (match) {
      const day = dayMap[match[1]];
      if (day !== undefined) {
        windows.push({
          day,
          startMin: parseInt(match[2], 10) * 60 + parseInt(match[3], 10),
          endMin: parseInt(match[4], 10) * 60 + parseInt(match[5], 10),
        });
      }
    }
  }
  return windows;
}

function checkChangeWindow(): string | null {
  const windows = parseWindows();
  if (windows.length === 0) return null;

  const now = new Date();
  const currentDay = now.getDay();
  const currentMin = now.getHours() * 60 + now.getMinutes();

  for (const w of windows) {
    if (w.day === currentDay && currentMin >= w.startMin && currentMin <= w.endMin) {
      return null; // Inside a window
    }
  }

  // Find next window
  const nextWindow = findNextWindow(windows);
  return `Changes are only allowed during maintenance windows. Next window: ${nextWindow}`;
}

function findNextWindow(windows: TimeWindow[]): string {
  const now = new Date();
  const currentDay = now.getDay();
  const currentMin = now.getHours() * 60 + now.getMinutes();

  // Check remaining days this week
  for (let offset = 0; offset < 7; offset++) {
    const checkDay = (currentDay + offset) % 7;
    for (const w of windows) {
      if (w.day === checkDay) {
        if (offset === 0 && currentMin >= w.endMin) continue;
        const dayName = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][w.day];
        return `${dayName} ${String(Math.floor(w.startMin / 60)).padStart(2, "0")}:${String(w.startMin % 60).padStart(2, "0")}`;
      }
    }
  }
  return "No upcoming windows configured";
}

// ─── Helpers ────────────────────────────────────────────────────

function hashToken(token: string): string {
  let hash = 0;
  for (let i = 0; i < token.length; i++) {
    const char = token.charCodeAt(i);
    hash = ((hash << 5) - hash + char) | 0;
  }
  return "usr_" + Math.abs(hash).toString(16).slice(0, 8);
}
