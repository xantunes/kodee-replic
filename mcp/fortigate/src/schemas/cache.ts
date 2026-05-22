import { ParsedModule } from "./parser.js";

interface CacheEntry {
  module: ParsedModule;
  timestamp: number;
}

const DEFAULT_TTL_MS = 5 * 60 * 1000; // 5 minutes

export class SchemaCache {
  private cache = new Map<string, CacheEntry>();

  constructor(private ttlMs: number = DEFAULT_TTL_MS) {}

  get(moduleName: string): ParsedModule | undefined {
    const entry = this.cache.get(moduleName);
    if (!entry) return undefined;

    if (Date.now() - entry.timestamp > this.ttlMs) {
      this.cache.delete(moduleName);
      return undefined;
    }

    return entry.module;
  }

  set(moduleName: string, module: ParsedModule): void {
    this.cache.set(moduleName, {
      module,
      timestamp: Date.now(),
    });
  }

  has(moduleName: string): boolean {
    return this.get(moduleName) !== undefined;
  }

  clear(): void {
    this.cache.clear();
  }

  size(): number {
    return this.cache.size;
  }
}

export const globalSchemaCache = new SchemaCache();
