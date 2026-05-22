/**
 * FortiOS response formatter
 * Converts raw JSON into human-readable markdown
 */

export function formatResponse(data: unknown): string {
  if (data === null || data === undefined) {
    return "*No data returned*";
  }

  if (typeof data !== "object") {
    return String(data);
  }

  // Handle FortiOS standard response wrapper
  const record = data as Record<string, unknown>;
  if (record.http_method || record.http_status) {
    const inner = record.results ?? record.result ?? record;
    return formatObject(inner);
  }

  // Array of objects → table
  if (Array.isArray(data)) {
    if (data.length === 0) return "*No items found*";
    if (data.length === 1) return formatObject(data[0]);
    return formatTable(data);
  }

  return formatObject(data);
}

function formatTable(items: unknown[]): string {
  const rows = items.slice(0, 50); // Limit to 50 for readability
  const firstRow = rows[0] as Record<string, unknown>;
  const keys = Object.keys(firstRow).filter((k) => !isNested(firstRow[k]));

  // Limit columns
  const displayKeys = keys.slice(0, 8);

  let md = "| " + displayKeys.join(" | ") + " |\n";
  md += "|" + displayKeys.map(() => " --- ").join("|") + "|\n";

  for (const item of rows) {
    const row = item as Record<string, unknown>;
    const values = displayKeys.map((k) => {
      const v = row[k];
      if (v === null || v === undefined) return "";
      if (typeof v === "object") return "[...]";
      const s = String(v).replace(/\|/g, "\\|").replace(/\n/g, " ");
      return s.length > 40 ? s.slice(0, 37) + "..." : s;
    });
    md += "| " + values.join(" | ") + " |\n";
  }

  if (items.length > 50) {
    md += `\n*... and ${items.length - 50} more items (use filters to narrow down)*`;
  }

  return md;
}

function formatObject(obj: unknown): string {
  if (obj === null || obj === undefined) return "*empty*";
  if (typeof obj !== "object") return String(obj);
  if (Array.isArray(obj)) {
    if (obj.length === 0) return "*empty list*";
    return obj.map((item, i) => `${i + 1}. ${formatInline(item)}`).join("\n");
  }

  const record = obj as Record<string, unknown>;
  let md = "";

  for (const [key, value] of Object.entries(record)) {
    if (value === null || value === undefined) continue;

    const label = key.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());

    if (typeof value === "object" && !Array.isArray(value)) {
      md += `\n**${label}:**\n${indent(formatObject(value))}\n`;
    } else if (Array.isArray(value)) {
      if (value.length === 0) {
        md += `- **${label}:** *(empty)*\n`;
      } else if (value.length > 10) {
        md += `- **${label}:** ${value.length} items\n`;
      } else {
        md += `- **${label}:** ${value.map((v) => formatInline(v)).join(", ")}\n`;
      }
    } else {
      md += `- **${label}:** ${String(value)}\n`;
    }
  }

  return md || "*empty object*";
}

function formatInline(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value !== "object") return String(value);
  if (Array.isArray(value)) return `[${value.length} items]`;
  const keys = Object.keys(value as object);
  if (keys.length === 0) return "{}";
  if (keys.includes("name")) return String((value as Record<string, unknown>).name);
  if (keys.includes("id")) return String((value as Record<string, unknown>).id);
  return `{${keys.slice(0, 3).join(", ")}${keys.length > 3 ? "..." : ""}}`;
}

function isNested(value: unknown): boolean {
  return value !== null && typeof value === "object";
}

function indent(text: string): string {
  return text
    .split("\n")
    .map((line) => (line.trim() ? "  " + line : line))
    .join("\n");
}
