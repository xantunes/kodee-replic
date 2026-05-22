import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { FortiOSClient } from "../client/fortios-client.js";
import { ParsedModule, TagEndpoints } from "../schemas/parser.js";
import { globalBackupManager } from "../backup/manager.js";
import { formatResponse } from "../utils/formatter.js";
import { fortiosString } from "../validation/fortios-formats.js";

// Registry of tool handlers
const toolHandlers = new Map<
  string,
  (args: Record<string, unknown>, client: FortiOSClient, dryRun: boolean) => Promise<unknown>
>();

/**
 * Register a custom tool handler
 */
export function registerToolHandler(
  name: string,
  handler: (args: Record<string, unknown>, client: FortiOSClient, dryRun: boolean) => Promise<unknown>
): void {
  toolHandlers.set(name, handler);
}

/**
 * Generate MCP tool definitions from a parsed module
 */
export function generateToolDefinitions(
  module: ParsedModule,
  _client: FortiOSClient,
  _dryRun: boolean
): Tool[] {
  const tools: Tool[] = [];

  for (const tag of module.tags) {
    const resourceName = tag.tag.split(".").pop() || tag.tag;
    const toolName = `fortios_${module.moduleName}_${resourceName}`.replace(/[^a-zA-Z0-9_]/g, "_");

    const tool: Tool = {
      name: toolName,
      description: `${tag.description}\n\nModule: ${module.moduleName}\nTag: ${tag.tag}`,
      inputSchema: generateInputSchema(tag) as Tool["inputSchema"],
    };

    // Register handler
    toolHandlers.set(toolName, (args, client, dryRun) =>
      handleTagOperation(tag, args, client, dryRun)
    );

    tools.push(tool);
  }

  return tools;
}

/**
 * Handle a tool call by name
 */
export async function handleToolCall(
  name: string,
  args: Record<string, unknown> | undefined,
  client: FortiOSClient,
  dryRun: boolean
): Promise<unknown> {
  const handler = toolHandlers.get(name);
  if (!handler) {
    throw new Error(`No handler registered for tool "${name}"`);
  }
  return handler(args || {}, client, dryRun);
}

/**
 * Generate JSON Schema for tool inputs based on endpoints
 */
function generateInputSchema(tag: TagEndpoints): {
  type: "object";
  properties: Record<string, unknown>;
  required: string[];
} {
  const properties: Record<string, unknown> = {
    operation: {
      type: "string",
      enum: ["list", "get", "create", "update", "delete"],
      description: "CRUD operation to perform",
    },
  };
  const required: string[] = ["operation"];

  // Add parameters from GET endpoint (most common)
  const getEndpoint = tag.endpoints.find((e) => e.method === "GET" && !e.path.includes("{"));
  if (getEndpoint?.operation.parameters && Array.isArray(getEndpoint.operation.parameters)) {
    for (const param of getEndpoint.operation.parameters) {
      if (param.in === "query" && param.name) {
        properties[param.name] = {
          type: (param.type as string) || "string",
          description: param.description || `${param.name} filter`,
        };
      }
    }
  }

  // Add ID parameter for get/update/delete
  const hasIdEndpoint = tag.endpoints.some(
    (e) => ["GET", "PUT", "DELETE"].includes(e.method) && e.path.includes("{")
  );
  if (hasIdEndpoint) {
    properties.id = {
      type: "string",
      description: "Object ID or name (required for get/update/delete)",
    };
  }

  // Add data parameter for create/update
  const hasBodyEndpoint = tag.endpoints.some(
    (e) => e.method === "POST" || e.method === "PUT"
  );
  if (hasBodyEndpoint) {
    properties.data = {
      type: "object",
      description: "Object data (required for create/update)",
    };
  }

  return { type: "object", properties, required };
}

/**
 * Handle CRUD operation for a tag
 */
async function handleTagOperation(
  tag: TagEndpoints,
  args: Record<string, unknown>,
  client: FortiOSClient,
  dryRun: boolean
): Promise<unknown> {
  const operation = args.operation as string;

  switch (operation) {
    case "list":
      return handleList(tag, args, client, dryRun);
    case "get":
      return handleGet(tag, args, client, dryRun);
    case "create":
      return handleCreate(tag, args, client, dryRun);
    case "update":
      return handleUpdate(tag, args, client, dryRun);
    case "delete":
      return handleDelete(tag, args, client, dryRun);
    default:
      throw new Error(`Unknown operation: ${operation}`);
  }
}

async function handleList(
  tag: TagEndpoints,
  args: Record<string, unknown>,
  client: FortiOSClient,
  dryRun: boolean
): Promise<unknown> {
  const endpoint = tag.endpoints.find((e) => e.method === "GET" && !e.path.includes("{"));
  if (!endpoint) throw new Error("List operation not supported");

  const params: Record<string, unknown> = { count: 1 };
  // Forward query params
  for (const key of Object.keys(args)) {
    if (key !== "operation" && key !== "id" && key !== "data") {
      params[key] = args[key];
    }
  }

  if (dryRun) {
    return { dryRun: true, operation: "list", path: endpoint.path, params };
  }

  const data = await fetchPaginated(endpoint.path, params, client);
  return formatResponse(data);
}

/**
 * Auto-paginate FortiOS list responses
 */
async function fetchPaginated(
  path: string,
  params: Record<string, unknown>,
  client: FortiOSClient,
  maxItems: number = 10000
): Promise<unknown[]> {
  const allResults: unknown[] = [];
  let start = 0;
  const limit = 1000;

  while (allResults.length < maxItems) {
    const pageParams = { ...params, start, limit };
    const response = (await client.get(path, { params: pageParams })) as {
      results?: unknown[];
      count?: number;
    };

    const results = response.results || [];
    allResults.push(...results);

    // If no results or less than limit, we're done
    if (results.length < limit) break;

    start += limit;

    // Safety: if total count known and we've fetched all
    if (response.count && allResults.length >= response.count) break;
  }

  return allResults;
}

async function handleGet(
  tag: TagEndpoints,
  args: Record<string, unknown>,
  client: FortiOSClient,
  dryRun: boolean
): Promise<unknown> {
  const id = args.id as string;
  if (!id) throw new Error("'id' is required for get operation");

  const endpoint = tag.endpoints.find(
    (e) => e.method === "GET" && e.path.includes("{")
  );
  if (!endpoint) throw new Error("Get operation not supported");

  const path = endpoint.path.replace(/{[^}]+}/, encodeURIComponent(id));

  if (dryRun) {
    return { dryRun: true, operation: "get", path };
  }

  const data = await client.get(path);
  return formatResponse(data);
}

async function handleCreate(
  tag: TagEndpoints,
  args: Record<string, unknown>,
  client: FortiOSClient,
  dryRun: boolean
): Promise<unknown> {
  const data = args.data as Record<string, unknown>;
  if (!data) throw new Error("'data' is required for create operation");

  // Validate data fields
  const validationErrors = validateFortiOSData(data);
  if (validationErrors.length > 0) {
    throw new Error(`Validation failed:\n${validationErrors.join("\n")}`);
  }

  const endpoint = tag.endpoints.find((e) => e.method === "POST");
  if (!endpoint) throw new Error("Create operation not supported");

  if (dryRun) {
    return { dryRun: true, operation: "create", path: endpoint.path, data };
  }

  // Save a record of the create operation for rollback awareness
  globalBackupManager.save(endpoint.path, data, "create");

  const result = await client.post(endpoint.path, { data });
  return formatResponse(result);
}

async function handleUpdate(
  tag: TagEndpoints,
  args: Record<string, unknown>,
  client: FortiOSClient,
  dryRun: boolean
): Promise<unknown> {
  const id = args.id as string;
  const data = args.data as Record<string, unknown>;
  if (!id) throw new Error("'id' is required for update operation");
  if (!data) throw new Error("'data' is required for update operation");

  // Validate data fields
  const validationErrors = validateFortiOSData(data);
  if (validationErrors.length > 0) {
    throw new Error(`Validation failed:\n${validationErrors.join("\n")}`);
  }

  const endpoint = tag.endpoints.find((e) => e.method === "PUT");
  if (!endpoint) throw new Error("Update operation not supported");

  const path = endpoint.path.replace(/{[^}]+}/, encodeURIComponent(id));

  // Backup current state before update
  try {
    const current = await client.get(path);
    globalBackupManager.save(path, current, "update");
  } catch {
    // If get fails, still proceed but note no backup
    globalBackupManager.save(path, null, "update_no_backup");
  }

  if (dryRun) {
    return { dryRun: true, operation: "update", path, data };
  }

  const result = await client.put(path, { data });
  return formatResponse(result);
}

async function handleDelete(
  tag: TagEndpoints,
  args: Record<string, unknown>,
  client: FortiOSClient,
  dryRun: boolean
): Promise<unknown> {
  const id = args.id as string;
  if (!id) throw new Error("'id' is required for delete operation");

  const endpoint = tag.endpoints.find((e) => e.method === "DELETE");
  if (!endpoint) throw new Error("Delete operation not supported");

  const path = endpoint.path.replace(/{[^}]+}/, encodeURIComponent(id));

  // Backup current state before delete
  try {
    const current = await client.get(path);
    globalBackupManager.save(path, current, "delete");
  } catch {
    globalBackupManager.save(path, null, "delete_no_backup");
  }

  if (dryRun) {
    return { dryRun: true, operation: "delete", path };
  }

  const result = await client.delete(path);
  return formatResponse(result);
}

/**
 * Validate object data for FortiOS-specific formats
 * Returns array of error messages (empty if valid)
 */
function validateFortiOSData(data: Record<string, unknown>): string[] {
  const errors: string[] = [];

  for (const [key, value] of Object.entries(data)) {
    if (value === null || value === undefined) continue;
    if (typeof value !== "string") continue;

    const validator = fortiosString(key);
    const result = validator.safeParse(value);
    if (!result.success) {
      errors.push(`- ${key}: ${result.error.errors[0]?.message || "invalid format"}`);
    }
  }

  return errors;
}
