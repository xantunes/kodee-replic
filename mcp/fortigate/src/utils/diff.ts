/**
 * Deep diff between two objects
 */

export interface DiffEntry {
  path: string;
  type: "added" | "removed" | "modified";
  old_value?: unknown;
  new_value?: unknown;
}

const IGNORED_KEYS = new Set([
  "q_origin_key",
  "uuid",
  "_gen_no",
  "dirty",
  "seq-num",
  "build",
  "http_method",
  "http_status",
  "vdom",
  "mkey",
]);

export function diffObjects(a: unknown, b: unknown, prefix = ""): DiffEntry[] {
  const diffs: DiffEntry[] = [];

  if (a === null || a === undefined || b === null || b === undefined) {
    if (a !== b) {
      diffs.push({
        path: prefix || "root",
        type: "modified",
        old_value: a,
        new_value: b,
      });
    }
    return diffs;
  }

  if (typeof a !== "object" || typeof b !== "object") {
    if (a !== b) {
      diffs.push({
        path: prefix || "root",
        type: "modified",
        old_value: a,
        new_value: b,
      });
    }
    return diffs;
  }

  if (Array.isArray(a) && Array.isArray(b)) {
    const maxLen = Math.max(a.length, b.length);
    for (let i = 0; i < maxLen; i++) {
      const path = prefix ? `${prefix}[${i}]` : `[${i}]`;
      if (i >= a.length) {
        diffs.push({ path, type: "added", new_value: b[i] });
      } else if (i >= b.length) {
        diffs.push({ path, type: "removed", old_value: a[i] });
      } else {
        diffs.push(...diffObjects(a[i], b[i], path));
      }
    }
    return diffs;
  }

  const objA = a as Record<string, unknown>;
  const objB = b as Record<string, unknown>;
  const allKeys = new Set([...Object.keys(objA), ...Object.keys(objB)]);

  for (const key of allKeys) {
    if (IGNORED_KEYS.has(key)) continue;

    const path = prefix ? `${prefix}.${key}` : key;
    const valA = objA[key];
    const valB = objB[key];

    if (!(key in objA)) {
      diffs.push({ path, type: "added", new_value: valB });
    } else if (!(key in objB)) {
      diffs.push({ path, type: "removed", old_value: valA });
    } else {
      diffs.push(...diffObjects(valA, valB, path));
    }
  }

  return diffs;
}

export function formatDiff(diffs: DiffEntry[]): string {
  if (diffs.length === 0) return "*No differences found*";

  let md = `### Differences (${diffs.length})\n\n`;
  for (const d of diffs) {
    if (d.type === "added") {
      md += `- **+ ${d.path}**: \`${JSON.stringify(d.new_value).slice(0, 80)}\`\n`;
    } else if (d.type === "removed") {
      md += `- **- ${d.path}**: \`${JSON.stringify(d.old_value).slice(0, 80)}\`\n`;
    } else {
      md += `- **~ ${d.path}**: \`${JSON.stringify(d.old_value).slice(0, 40)}\` → \`${JSON.stringify(d.new_value).slice(0, 40)}\`\n`;
    }
  }
  return md;
}
