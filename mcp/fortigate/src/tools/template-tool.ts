import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { FortiOSClient } from "../client/fortios-client.js";
import { readFileSync, readdirSync } from "fs";
import { resolve } from "path";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const TEMPLATES_DIR = resolve(__dirname, "../../templates");

export const TEMPLATE_APPLY_TOOL_NAME = "fortios_template_apply";
export const TEMPLATE_LIST_TOOL_NAME = "fortios_template_list";

export interface Template {
  name: string;
  description: string;
  parameters: Record<string, { type: string; required: boolean; description: string }>;
  steps: Array<{
    tool: string;
    operation: string;
    data: Record<string, unknown>;
  }>;
}

function loadTemplate(name: string): Template {
  const path = resolve(TEMPLATES_DIR, `${name}.json`);
  const content = readFileSync(path, "utf-8");
  return JSON.parse(content) as Template;
}

function listTemplates(): Array<{ name: string; description: string }> {
  const files = readdirSync(TEMPLATES_DIR).filter((f) => f.endsWith(".json"));
  return files.map((f) => {
    const t = JSON.parse(readFileSync(resolve(TEMPLATES_DIR, f), "utf-8")) as Template;
    return { name: t.name, description: t.description };
  });
}

function renderTemplate(data: Record<string, unknown>, params: Record<string, string>): Record<string, unknown> {
  const json = JSON.stringify(data);
  let rendered = json;
  for (const [key, value] of Object.entries(params)) {
    rendered = rendered.replace(new RegExp(`\\{\\{${key}\\}\\}`, "g"), String(value));
  }
  return JSON.parse(rendered) as Record<string, unknown>;
}

function validateParams(template: Template, params: Record<string, unknown>): string[] {
  const errors: string[] = [];
  for (const [key, spec] of Object.entries(template.parameters)) {
    if (spec.required && (params[key] === undefined || params[key] === "")) {
      errors.push(`Missing required parameter: ${key} (${spec.description})`);
    }
  }
  for (const key of Object.keys(params)) {
    if (!template.parameters[key]) {
      errors.push(`Unknown parameter: ${key}`);
    }
  }
  return errors;
}

export function getTemplateApplyTool(): Tool {
  return {
    name: TEMPLATE_APPLY_TOOL_NAME,
    description:
      "Apply a pre-defined configuration template. " +
      "Templates: site-to-site-vpn, dmz-standard, guest-wifi.",
    inputSchema: {
      type: "object",
      properties: {
        template_name: {
          type: "string",
          description: "Template name (e.g., site-to-site-vpn, dmz-standard, guest-wifi)",
        },
        parameters: {
          type: "object",
          description: "Template parameters (varies by template)",
        },
      },
      required: ["template_name", "parameters"],
    } as Tool["inputSchema"],
  };
}

export function getTemplateListTool(): Tool {
  return {
    name: TEMPLATE_LIST_TOOL_NAME,
    description: "List available configuration templates with their descriptions.",
    inputSchema: { type: "object", properties: {} } as Tool["inputSchema"],
  };
}

export async function handleTemplateApply(
  args: Record<string, unknown>,
  client: FortiOSClient,
  dryRun: boolean
): Promise<unknown> {
  const templateName = args.template_name as string;
  const params = (args.parameters || {}) as Record<string, string>;

  let template: Template;
  try {
    template = loadTemplate(templateName);
  } catch {
    return {
      status: "error",
      message: `Template "${templateName}" not found. Use fortios_template_list to see available templates.`,
    };
  }

  const validationErrors = validateParams(template, params);
  if (validationErrors.length > 0) {
    return { status: "error", message: "Validation failed", errors: validationErrors };
  }

  const results = [];
  let success = 0;
  let failed = 0;

  for (const step of template.steps) {
    const path = "/" + step.tool.replace("fortios_", "").replace(/_/g, "/");
    const data = renderTemplate(step.data, params);

    if (dryRun) {
      results.push({ status: "dry_run", step: step.tool, path, data });
      success++;
      continue;
    }

    try {
      if (step.operation === "create") {
        await client.post(path, { data });
      } else if (step.operation === "update") {
        const id = String(data.name || data.id || "");
        await client.put(`${path}/${encodeURIComponent(id)}`, { data });
      }
      results.push({ status: "success", step: step.tool });
      success++;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      results.push({ status: "error", step: step.tool, error: message });
      failed++;
    }
  }

  return {
    status: failed === 0 ? "success" : "partial",
    template: templateName,
    total_steps: template.steps.length,
    success,
    failed,
    results,
  };
}

export async function handleTemplateList(): Promise<unknown> {
  return {
    status: "success",
    templates: listTemplates(),
  };
}
