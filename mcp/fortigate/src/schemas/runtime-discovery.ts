import { FortiOSClient } from "../client/fortios-client.js";
import { SwaggerSchema, SwaggerOperation } from "./loader.js";

/**
 * Runtime API discovery - introspects the connected FortiGate
 * to discover available endpoints when local schemas are unavailable
 */

export interface DiscoveredEndpoint {
  path: string;
  methods: string[];
  description?: string;
}

/**
 * Attempt to discover API schema from FortiOS CMDB
 * FortiOS doesn't have a formal schema endpoint, but we can
 * probe common endpoints to discover what's available
 */
export async function discoverApiEndpoints(
  client: FortiOSClient,
  knownPaths: string[]
): Promise<DiscoveredEndpoint[]> {
  const discovered: DiscoveredEndpoint[] = [];

  for (const path of knownPaths) {
    try {
      const response = await client.get(path, { params: { count: 1, limit: 1 } });
      if (response) {
        discovered.push({
          path,
          methods: ["GET"],
          description: "Discovered at runtime",
        });
      }
    } catch (error: unknown) {
      // 404 = endpoint doesn't exist, 403 = no permission
      // Both mean we shouldn't expose this endpoint
      const status = extractStatusCode(error);
      if (status === 200 || status === 401) {
        // 401 means endpoint exists but needs auth - still expose it
        discovered.push({
          path,
          methods: ["GET"],
          description: "Discovered at runtime (auth required for details)",
        });
      }
    }
  }

  return discovered;
}

function extractStatusCode(error: unknown): number | undefined {
  if (error && typeof error === "object") {
    const e = error as { statusCode?: number; response?: { status?: number } };
    return e.statusCode ?? e.response?.status;
  }
  return undefined;
}

/**
 * Build a minimal Swagger-like schema from discovered endpoints
 */
export function buildDynamicSchema(
  endpoints: DiscoveredEndpoint[],
  moduleName: string
): SwaggerSchema {
  const paths: Record<string, Record<string, SwaggerOperation>> = {};
  const tags: Array<{ name: string; description: string }> = [];

  for (const ep of endpoints) {
    paths[ep.path] = {};
    const tagName = `${moduleName}.${ep.path.split("/").pop() || "unknown"}`;

    tags.push({
      name: tagName,
      description: ep.description || `${tagName} configuration`,
    });

    for (const method of ep.methods) {
      paths[ep.path][method.toLowerCase()] = {
        tags: [tagName],
        summary: `${method} ${ep.path}`,
        responses: {
          "200": { description: "OK" },
        },
      };
    }
  }

  return {
    swagger: "2.0",
    info: {
      title: `FortiOS ${moduleName} (Runtime Discovery)`,
      description: "Auto-discovered endpoints",
      version: "runtime",
    },
    basePath: "/api/v2/cmdb",
    tags,
    paths,
  };
}
