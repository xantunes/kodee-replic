import { readdirSync, existsSync } from "fs";
import { resolve } from "path";
import {
  VersionInfo,
  parseVersion,
  compareVersions,
  versionToFolderName,
} from "./version-detector.js";

/**
 * Discovers available schema versions from filesystem
 */
export function discoverAvailableVersions(schemaBaseDir: string): VersionInfo[] {
  if (!existsSync(schemaBaseDir)) return [];

  const entries = readdirSync(schemaBaseDir, { withFileTypes: true });
  const versions: VersionInfo[] = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;

    const parsed = parseVersion(entry.name);
    if (parsed) {
      versions.push(parsed);
    }
  }

  // Sort by version ascending
  versions.sort(compareVersions);
  return versions;
}

/**
 * Select the best matching schema version for a target FortiOS version
 * Strategy:
 * 1. Exact major.minor match → use it
 * 2. Closest lower version → use it (backward compatible)
 * 3. Closest higher version → use it with warning
 * 4. No schemas → null
 */
export function selectSchemaVersion(
  target: VersionInfo,
  available: VersionInfo[]
): { selected: VersionInfo; warning?: string } | null {
  if (available.length === 0) return null;

  // Exact match on major.minor
  const exactMatch = available.find(
    (v) => v.major === target.major && v.minor === target.minor
  );
  if (exactMatch) {
    return { selected: exactMatch };
  }

  // Find closest lower version (prefer older = more stable/compatible)
  const lowerVersions = available.filter(
    (v) =>
      v.major < target.major ||
      (v.major === target.major && v.minor < target.minor)
  );

  if (lowerVersions.length > 0) {
    const closestLower = lowerVersions[lowerVersions.length - 1];
    return {
      selected: closestLower,
      warning: `FortiOS ${versionToFolderName(target)} detected but using schemas ${versionToFolderName(closestLower)}. Some newer endpoints may be missing.`,
    };
  }

  // Find closest higher version
  const higherVersions = available.filter(
    (v) =>
      v.major > target.major ||
      (v.major === target.major && v.minor > target.minor)
  );

  if (higherVersions.length > 0) {
    const closestHigher = higherVersions[0];
    return {
      selected: closestHigher,
      warning: `FortiOS ${versionToFolderName(target)} detected but using schemas ${versionToFolderName(closestHigher)}. Some endpoints may not exist on your device.`,
    };
  }

  return null;
}

/**
 * Get schema directory path for a version
 */
export function getSchemaDir(
  baseDir: string,
  version: VersionInfo
): string {
  return resolve(baseDir, versionToFolderName(version));
}
