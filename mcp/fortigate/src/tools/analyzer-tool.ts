import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { FortiOSClient } from "../client/fortios-client.js";

export const ANALYZER_TOOL_NAME = "fortios_analyze";

export function getAnalyzerTool(): Tool {
  return {
    name: ANALYZER_TOOL_NAME,
    description:
      "Analyze FortiGate configuration for security issues, best practice violations, " +
      "and optimization opportunities. Checks firewall policies, objects, and system settings.",
    inputSchema: {
      type: "object",
      properties: {
        scope: {
          type: "string",
          enum: ["security", "hygiene", "all"],
          description: "Analysis scope: security, hygiene, or all",
        },
      },
    } as Tool["inputSchema"],
  };
}

interface Finding {
  severity: "critical" | "warning" | "info";
  category: string;
  message: string;
  remediation: string;
  object?: string;
}

export async function handleAnalyze(
  args: Record<string, unknown>,
  client: FortiOSClient
): Promise<unknown> {
  const scope = (args.scope as string) || "all";
  const findings: Finding[] = [];

  if (scope === "security" || scope === "all") {
    await analyzeSecurity(findings, client);
  }

  if (scope === "hygiene" || scope === "all") {
    await analyzeHygiene(findings, client);
  }

  const critical = findings.filter((f) => f.severity === "critical").length;
  const warning = findings.filter((f) => f.severity === "warning").length;
  const info = findings.filter((f) => f.severity === "info").length;

  return {
    status: "success",
    scope,
    summary: { critical, warning, info, total: findings.length },
    findings,
  };
}

async function analyzeSecurity(findings: Finding[], client: FortiOSClient): Promise<void> {
  // Check firewall policies
  try {
    const resp = (await client.get("/firewall/policy", { params: { count: 1 } })) as {
      results?: Array<Record<string, unknown>>;
    };
    const policies = resp.results || [];

    for (const policy of policies) {
      const name = String(policy.name || policy.policyid || "unknown");
      const src = policy.srcaddr as Array<{ name?: string }> | undefined;
      const dst = policy.dstaddr as Array<{ name?: string }> | undefined;
      const action = policy.action as string | undefined;
      const nat = policy.nat as string | undefined;
      const log = policy.logtraffic as string | undefined;
      const status = policy.status as string | undefined;

      // any-any without NAT
      const isAnySrc = src?.some((a) => a.name === "all");
      const isAnyDst = dst?.some((a) => a.name === "all");
      if (isAnySrc && isAnyDst && action === "accept" && nat !== "enable") {
        findings.push({
          severity: "critical",
          category: "firewall.policy",
          message: `Policy "${name}" allows any-to-any without NAT`,
          remediation: "Restrict sources/destinations or enable NAT for internet-bound traffic",
          object: name,
        });
      }

      // No logging
      if (log === "disable" || !log) {
        findings.push({
          severity: "warning",
          category: "firewall.policy",
          message: `Policy "${name}" has logging disabled`,
          remediation: "Enable logtraffic to 'all' or 'utm' for visibility",
          object: name,
        });
      }

      // Disabled policy
      if (status === "disable") {
        findings.push({
          severity: "info",
          category: "firewall.policy",
          message: `Policy "${name}" is disabled`,
          remediation: "Review if still needed or remove stale policies",
          object: name,
        });
      }
    }
  } catch {
    // Skip if no access
  }

  // Check admin settings
  try {
    const admin = (await client.get("/system/admin", { params: { count: 1 } })) as {
      results?: Array<Record<string, unknown>>;
    };
    for (const user of admin.results || []) {
      const name = String(user.name || "unknown");
      const accprofile = user.accprofile as string | undefined;
      const trustedhosts = user.trustedhosts as Array<unknown> | undefined;

      if (accprofile === "super_admin" && (!trustedhosts || trustedhosts.length === 0)) {
        findings.push({
          severity: "critical",
          category: "system.admin",
          message: `Admin "${name}" is super_admin without trusted hosts restriction`,
          remediation: "Add trustedhosts to restrict admin access by IP",
          object: name,
        });
      }
    }
  } catch {
    // Skip
  }
}

async function analyzeHygiene(findings: Finding[], client: FortiOSClient): Promise<void> {
  // Check for duplicate policies
  try {
    const resp = (await client.get("/firewall/policy", { params: { count: 1 } })) as {
      results?: Array<Record<string, unknown>>;
    };
    const policies = resp.results || [];
    const signatures = new Map<string, string>();

    for (const policy of policies) {
      const src = (policy.srcaddr as Array<{ name?: string }> | undefined)?.map((a) => a.name).sort().join(",");
      const dst = (policy.dstaddr as Array<{ name?: string }> | undefined)?.map((a) => a.name).sort().join(",");
      const svc = (policy.service as Array<{ name?: string }> | undefined)?.map((a) => a.name).sort().join(",");
      const action = policy.action;
      const sig = `${src}|${dst}|${svc}|${action}`;

      if (signatures.has(sig)) {
        findings.push({
          severity: "warning",
          category: "firewall.policy",
          message: `Duplicate policy detected: "${policy.name}" matches "${signatures.get(sig)}"`,
          remediation: "Consolidate or remove duplicate rules",
          object: String(policy.name),
        });
      } else {
        signatures.set(sig, String(policy.name));
      }
    }
  } catch {
    // Skip
  }

  // Check interface without IP
  try {
    const ifaces = (await client.get("/system/interface", { params: { count: 1 } })) as {
      results?: Array<Record<string, unknown>>;
    };
    for (const iface of ifaces.results || []) {
      const name = String(iface.name || "unknown");
      const ip = iface.ip as string | undefined;
      const type = iface.type as string | undefined;
      const status = iface.status as string | undefined;

      if (type === "physical" && status === "up" && (!ip || ip === "0.0.0.0 0.0.0.0")) {
        findings.push({
          severity: "info",
          category: "system.interface",
          message: `Interface "${name}" is up but has no IP`,
          remediation: "Assign IP or verify if interface should be down",
          object: name,
        });
      }
    }
  } catch {
    // Skip
  }
}
