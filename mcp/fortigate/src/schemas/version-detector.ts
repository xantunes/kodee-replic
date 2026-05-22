import { FortiOSClient } from "../client/fortios-client.js";

/**
 * Detects FortiOS version from connected device
 */
export interface VersionInfo {
  major: number;
  minor: number;
  patch: number;
  raw: string;
}

/**
 * Parse FortiOS version string like "v7.4.9" or "7.4.9"
 */
export function parseVersion(versionStr: string): VersionInfo | null {
  // Match patterns like: v7.4.9, 7.4.9, 7.2, v7.2, FortiOS v7.4.9 build1234
  const match = versionStr.match(/v?(\d+)\.(\d+)(?:\.(\d+))?/);
  if (!match) return null;

  return {
    major: parseInt(match[1], 10),
    minor: parseInt(match[2], 10),
    patch: match[3] ? parseInt(match[3], 10) : 0,
    raw: match[3] ? `v${match[1]}.${match[2]}.${match[3]}` : `v${match[1]}.${match[2]}`,
  };
}

/**
 * Detect FortiOS version from API
 */
export async function detectFortiOSVersion(
  client: FortiOSClient
): Promise<VersionInfo | null> {
  try {
    const status = (await client.monitorGet("/system/status")) as {
      version?: string;
    };
    if (status.version) {
      return parseVersion(status.version);
    }
  } catch {
    // Failed to detect version
  }
  return null;
}

/**
 * Compare two versions
 * Returns: negative if a < b, 0 if equal, positive if a > b
 */
export function compareVersions(a: VersionInfo, b: VersionInfo): number {
  if (a.major !== b.major) return a.major - b.major;
  if (a.minor !== b.minor) return a.minor - b.minor;
  return a.patch - b.patch;
}

/**
 * Format version as string for folder name
 */
export function versionToFolderName(v: VersionInfo): string {
  return `${v.major}.${v.minor}`;
}

/**
 * Available schema versions (hardcoded based on existing schema folders)
 * Will be discovered at runtime
 */
export function getAvailableVersions(_schemaBaseDir: string): VersionInfo[] {
  // Will be populated by directory listing
  return [];
}
