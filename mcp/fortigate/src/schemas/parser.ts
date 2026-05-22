import {
  SwaggerSchema,
  SwaggerOperation,
} from "./loader.js";

export interface Endpoint {
  path: string;
  method: "GET" | "POST" | "PUT" | "DELETE";
  operation: SwaggerOperation;
}

export interface TagEndpoints {
  tag: string;
  description: string;
  endpoints: Endpoint[];
}

export interface ParsedModule {
  moduleName: string;
  tags: TagEndpoints[];
}

/**
 * Parse a Swagger schema into structured module/tag/endpoint hierarchy
 */
export function parseSchema(schema: SwaggerSchema, moduleName: string): ParsedModule {
  const tagMap = new Map<string, TagEndpoints>();

  // Initialize tags from schema.tags
  for (const tag of schema.tags || []) {
    tagMap.set(tag.name, {
      tag: tag.name,
      description: tag.description || `${tag.name} configuration`,
      endpoints: [],
    });
  }

  // Group endpoints by tag
  for (const [path, methods] of Object.entries(schema.paths)) {
    for (const [method, operation] of Object.entries(methods)) {
      if (!operation || typeof operation !== "object") continue;
      const op = operation as SwaggerOperation;
      if (!op.tags || op.tags.length === 0) continue;

      const tagName = op.tags[0];
      let tagGroup = tagMap.get(tagName);

      if (!tagGroup) {
        tagGroup = {
          tag: tagName,
          description: `${tagName} configuration`,
          endpoints: [],
        };
        tagMap.set(tagName, tagGroup);
      }

      tagGroup.endpoints.push({
        path,
        method: method.toUpperCase() as "GET" | "POST" | "PUT" | "DELETE",
        operation: op,
      });
    }
  }

  return {
    moduleName,
    tags: Array.from(tagMap.values()),
  };
}

/**
 * Extract resource name from tag
 * e.g., "firewall.policy" -> "policy"
 */
export function getResourceName(tag: string): string {
  const parts = tag.split(".");
  const lastPart = parts[parts.length - 1];
  // Handle sub-resources like "firewall/ippool"
  return lastPart.replace(/\//g, "_");
}

/**
 * Generate a clean tool name from module and resource
 * e.g., module="firewall", resource="policy" -> "fortios_firewall_policy"
 */
export function generateToolName(moduleName: string, resourceName: string): string {
  const cleanModule = moduleName.replace(/[^a-zA-Z0-9]/g, "_");
  const cleanResource = resourceName.replace(/[^a-zA-Z0-9]/g, "_");
  return `fortios_${cleanModule}_${cleanResource}`;
}
