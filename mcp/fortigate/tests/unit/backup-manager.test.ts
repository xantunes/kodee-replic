import assert from "node:assert";
import test from "node:test";
import { BackupManager } from "../../src/backup/manager.js";

test("BackupManager stores and retrieves backup", () => {
  const manager = new BackupManager();
  const backup = { path: "/firewall/policy/1", data: { name: "test-policy" } };

  manager.save(backup.path, backup.data);
  const retrieved = manager.getLast();

  assert.equal(retrieved?.path, backup.path);
  assert.deepStrictEqual(retrieved?.data, backup.data);
  assert.equal(typeof retrieved?.timestamp, "number");
});

test("BackupManager overwrites previous backup", () => {
  const manager = new BackupManager();
  manager.save("/firewall/policy/1", { name: "old" });
  manager.save("/firewall/policy/2", { name: "new" });

  const last = manager.getLast();
  assert.equal(last?.path, "/firewall/policy/2");
  assert.deepStrictEqual(last?.data, { name: "new" });
});

test("BackupManager returns undefined when empty", () => {
  const manager = new BackupManager();
  assert.equal(manager.getLast(), undefined);
});

test("BackupManager clears backups", () => {
  const manager = new BackupManager();
  manager.save("/test", { data: true });
  manager.clear();
  assert.equal(manager.getLast(), undefined);
});

test("BackupManager hasBackup returns correct state", () => {
  const manager = new BackupManager();
  assert.equal(manager.hasBackup(), false);
  manager.save("/test", { data: true });
  assert.equal(manager.hasBackup(), true);
});
