import { readFileSync, readdirSync } from "fs";
import { resolve, join } from "path";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

export interface SwaggerSchema {
  swagger: string;
  info: {
    title: string;
    description: string;
    version: string;
  };
  basePath: string;
  tags: Array<{
    name: string;
    description: string;
  }>;
  paths: Record<string, SwaggerPath>;
  definitions?: Record<string, unknown>;
}

export interface SwaggerPath {
  get?: SwaggerOperation;
  post?: SwaggerOperation;
  put?: SwaggerOperation;
  delete?: SwaggerOperation;
}

export interface SwaggerOperation {
  tags: string[];
  summary: string;
  description?: string;
  operationId?: string;
  consumes?: string[];
  produces?: string[];
  parameters?: SwaggerParameter[];
  responses: Record<string, SwaggerResponse>;
}

export interface SwaggerParameter {
  name: string;
  in: "query" | "path" | "body" | "header" | "formData";
  description?: string;
  required?: boolean;
  type?: string;
  schema?: unknown;
}

export interface SwaggerResponse {
  description: string;
  schema?: unknown;
}

/**
 * Load all Swagger JSON files from a versioned schemas directory
 */
export function loadAllSchemas(schemaDir?: string): SwaggerSchema[] {
  const dir = schemaDir || resolve(__dirname, "../../schemas/7.4");
  const files = readdirSync(dir).filter((f) => f.endsWith(".json"));

  const schemas: SwaggerSchema[] = [];
  for (const file of files) {
    try {
      const schema = loadSchema(join(dir, file));
      if (schema.info && schema.paths) {
        schemas.push(schema);
      }
    } catch {
      // Skip malformed schema files
    }
  }
  return schemas;
}

/**
 * Load a single Swagger JSON file
 */
export function loadSchema(filePath: string): SwaggerSchema {
  const content = readFileSync(filePath, "utf-8");
  return JSON.parse(content) as SwaggerSchema;
}

/**
 * Get module name from filename
 * e.g., "FortiOS 7.4 FortiOS 7.4.9 Configuration API firewall.json" -> "firewall"
 */
export function getModuleName(filename: string): string {
  const match = filename.match(/Configuration API ([^\.]+)\.json$/);
  return match ? match[1] : filename.replace(/\.json$/, "");
}
