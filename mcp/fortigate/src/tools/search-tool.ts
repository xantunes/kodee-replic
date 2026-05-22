import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { FortiOSClient } from "../client/fortios-client.js";
import { loadAllSchemas, getModuleName } from "../schemas/loader.js";
import { parseSchema } from "../schemas/parser.js";

export const SEARCH_TOOL_NAME = "fortios_search";

export function getSearchTool(): Tool {
  return {
    name: SEARCH_TOOL_NAME,
    description:
      "Search for objects across FortiOS modules by name, IP, or keyword. " +
      "Searches in firewall addresses, policies, interfaces, services, and more.",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Search term (name, IP address, or keyword)",
        },
        modules: {
          type: "array",
          items: { type: "string" },
          description: "Optional: limit search to specific modules (e.g., ['firewall', 'system'])",
        },
        maxResults: {
          type: "number",
          description: "Maximum results per module (default: 20)",
        },
      },
      required: ["query"],
    } as Tool["inputSchema"],
  };
}

export async function handleSearch(
  args: Record<string, unknown>,
  client: FortiOSClient
): Promise<unknown> {
  const query = String(args.query || "").toLowerCase();
  if (!query) {
    return { status: "error", message: "Query is required" };
  }

  const filterModules = args.modules as string[] | undefined;
  const maxResults = (args.maxResults as number) || 20;

  const schemas = loadAllSchemas();
  const results: Array<{
    module: string;
    tag: string;
    matches: Array<Record<string, unknown>>;
  }> = [];

  for (const schema of schemas) {
    const moduleName = getModuleName(schema.info.title || "unknown");

    if (filterModules && !filterModules.includes(moduleName)) continue;

    const parsed = parseSchema(schema, moduleName);

    for (const tag of parsed.tags) {
      const listEndpoint = tag.endpoints.find(
        (e) => e.method === "GET" && !e.path.includes("{")
      );
      if (!listEndpoint) continue;

      try {
        const response = (await client.get(listEndpoint.path, {
          params: { filter: `name==${query}`, count: 1, limit: maxResults },
        })) as { results?: Record<string, unknown>[] };

        const items = response.results || [];
        const matches = items.filter((item) => matchesQuery(item, query));

        if (matches.length > 0) {
          results.push({
            module: moduleName,
            tag: tag.tag,
            matches: matches.slice(0, maxResults),
          });
        }
      } catch {
        // Skip modules that fail (permissions, missing endpoints)
        continue;
      }
    }
  }

  return {
    status: "success",
    query,
    totalMatches: results.reduce((sum, r) => sum + r.matches.length, 0),
    modulesSearched: schemas.length,
    results,
  };
}

function matchesQuery(item: Record<string, unknown>, query: string): boolean {
  for (const [, value] of Object.entries(item)) {
    if (value === null || value === undefined) continue;
    const str = String(value).toLowerCase();
    if (str.includes(query)) return true;
  }
  return false;
}
