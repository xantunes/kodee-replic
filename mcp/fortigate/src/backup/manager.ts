/**
 * Session-based configuration backup manager
 * Stores backups in memory for rollback support
 */

export interface BackupEntry {
  path: string;
  data: unknown;
  timestamp: number;
  operation: string;
}

export class BackupManager {
  private backups: BackupEntry[] = [];

  /**
   * Save a configuration snapshot before modification
   */
  save(path: string, data: unknown, operation: string = "unknown"): void {
    this.backups.push({
      path,
      data,
      timestamp: Date.now(),
      operation,
    });
  }

  /**
   * Get the most recent backup
   */
  getLast(): BackupEntry | undefined {
    return this.backups.length > 0
      ? this.backups[this.backups.length - 1]
      : undefined;
  }

  /**
   * Get all backups
   */
  getAll(): BackupEntry[] {
    return [...this.backups];
  }

  /**
   * Check if any backup exists
   */
  hasBackup(): boolean {
    return this.backups.length > 0;
  }

  /**
   * Remove the last backup (after successful rollback)
   */
  pop(): BackupEntry | undefined {
    return this.backups.pop();
  }

  /**
   * Clear all backups
   */
  clear(): void {
    this.backups = [];
  }

  /**
   * Get count of stored backups
   */
  size(): number {
    return this.backups.length;
  }
}

// Global singleton for the session
export const globalBackupManager = new BackupManager();
