import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { FortiOSClient } from "../client/fortios-client.js";

export const DEPENDENCY_TOOL_NAME = "fortios_dependencies";

export function getDependencyTool(): Tool {
  return {
    name: DEPENDENCY_TOOL_NAME,
    description:
      "Find dependencies between FortiOS objects. " +
      "Discover which policies use an address, find orphan objects, or analyze impact of deletion.",
    inputSchema: {
      type: "object",
      properties: {
        mode: {
          type: "string",
          enum: ["used_by", "orphans"],
          description: "used_by: find what uses this object; orphans: find unused objects",
        },
        object_type: {
          type: "string",
          description: "Object type: address, addrgrp, service, service-group, vip, ippool",
        },
        object_name: {
          type: "string",
          description: "Object name (required for used_by mode)",
        },
      },
      required: ["mode"],
    } as Tool["inputSchema"],
  };
}

export async function handleDependencies(
  args: Record<string, unknown>,
  client: FortiOSClient
): Promise<unknown> {
  const mode = args.mode as "used_by" | "orphans";

  if (mode === "used_by") {
    const objType = args.object_type as string;
    const objName = args.object_name as string;
    if (!objType || !objName) {
      return { status: "error", message: "object_type and object_name required for used_by mode" };
    }
    return findUsedBy(objType, objName, client);
  }

  if (mode === "orphans") {
    return findOrphans(client);
  }

  return { status: "error", message: "Invalid mode" };
}

async function findUsedBy(
  objType: string,
  objName: string,
  client: FortiOSClient
): Promise<unknown> {
  const users: Array<{ type: string; name: string; field: string }> = [];

  // Search firewall policies for references
  try {
    const policies = (await client.get("/firewall/policy", { params: { count: 1 } })) as {
      results?: Array<Record<string, unknown>>;
    };
    for (const policy of policies.results || []) {
      for (const field of ["srcaddr", "dstaddr", "service"]) {
        const refs = policy[field] as Array<{ name?: string }> | undefined;
        if (refs && Array.isArray(refs)) {
          for (const ref of refs) {
            if (ref.name === objName) {
              users.push({
                type: "firewall.policy",
                name: String(policy.name || policy.policyid || "unknown"),
                field,
              });
            }
          }
        }
      }
    }
  } catch {
    // Skip if policies not accessible
  }

  // Search NAT/VIP references
  if (objType === "vip") {
    try {
      const policies = (await client.get("/firewall/policy", { params: { count: 1 } })) as {
        results?: Array<Record<string, unknown>>;
      };
      for (const policy of policies.results || []) {
        const nat = policy.nat as string | undefined;
        const ippool = policy.ippool as string | undefined;
        if (nat === "enable" || ippool === "enable") {
          // Check dstaddr for VIP
          const dstaddr = policy.dstaddr as Array<{ name?: string }> | undefined;
          if (dstaddr && Array.isArray(dstaddr)) {
            for (const ref of dstaddr) {
              if (ref.name === objName) {
                users.push({
                  type: "firewall.policy",
                  name: String(policy.name || policy.policyid || "unknown"),
                  field: "vip-dst",
                });
              }
            }
          }
        }
      }
    } catch {
      // Skip
    }
  }

  return {
    status: "success",
    object: { type: objType, name: objName },
    used_by_count: users.length,
    used_by: users,
    safe_to_delete: users.length === 0,
  };
}

async function findOrphans(client: FortiOSClient): Promise<unknown> {
  const orphans: Array<{ type: string; name: string }> = [];

  // Helper to collect all object names from a module
  async function getObjectNames(path: string): Promise<string[]> {
    try {
      const resp = (await client.get(path, { params: { count: 1 } })) as {
        results?: Array<{ name?: string }>;
      };
      return (resp.results || []).map((r) => r.name || "").filter(Boolean);
    } catch {
      return [];
    }
  }

  // Helper to collect all referenced names from policies
  async function getReferencedNames(field: string): Promise<Set<string>> {
    const refs = new Set<string>();
    try {
      const policies = (await client.get("/firewall/policy", { params: { count: 1 } })) as {
        results?: Array<Record<string, unknown>>;
      };
      for (const policy of policies.results || []) {
        const items = policy[field] as Array<{ name?: string }> | undefined;
        if (items && Array.isArray(items)) {
          for (const item of items) {
            if (item.name) refs.add(item.name);
          }
        }
      }
    } catch {
      // Skip
    }
    return refs;
  }

  // Find orphan addresses
  const [addrNames, srcRefs, dstRefs] = await Promise.all([
    getObjectNames("/firewall/address"),
    getReferencedNames("srcaddr"),
    getReferencedNames("dstaddr"),
  ]);
  const allAddrRefs = new Set([...srcRefs, ...dstRefs]);
  for (const name of addrNames) {
    if (!allAddrRefs.has(name)) {
      orphans.push({ type: "firewall.address", name });
    }
  }

  // Find orphan services
  const [svcNames, svcRefs] = await Promise.all([
    getObjectNames("/firewall/service/custom"),
    getReferencedNames("service"),
  ]);
  for (const name of svcNames) {
    if (!svcRefs.has(name)) {
      orphans.push({ type: "firewall.service/custom", name });
    }
  }

  return {
    status: "success",
    orphan_count: orphans.length,
    orphans,
  };
}
