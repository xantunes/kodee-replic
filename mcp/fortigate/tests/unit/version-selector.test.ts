import assert from "node:assert";
import test from "node:test";
import { selectSchemaVersion } from "../../src/schemas/version-selector.js";
import { VersionInfo, versionToFolderName } from "../../src/schemas/version-detector.js";

const v70: VersionInfo = { major: 7, minor: 0, patch: 0, raw: "v7.0.0" };
const v72: VersionInfo = { major: 7, minor: 2, patch: 0, raw: "v7.2.0" };
const v74: VersionInfo = { major: 7, minor: 4, patch: 0, raw: "v7.4.0" };
const v76: VersionInfo = { major: 7, minor: 6, patch: 0, raw: "v7.6.0" };

test("selectSchemaVersion returns exact match", () => {
  const result = selectSchemaVersion(v72, [v70, v72, v74]);
  assert.ok(result);
  assert.equal(result!.selected.major, 7);
  assert.equal(result!.selected.minor, 2);
  assert.equal(result!.warning, undefined);
});

test("selectSchemaVersion returns closest lower when no exact", () => {
  const result = selectSchemaVersion(v76, [v70, v72, v74]);
  assert.ok(result);
  assert.equal(result!.selected.minor, 4);
  assert.ok(result!.warning?.includes("7.6"));
});

test("selectSchemaVersion returns closest higher when no lower", () => {
  const result = selectSchemaVersion(v70, [v72, v74]);
  assert.ok(result);
  assert.equal(result!.selected.minor, 2);
  assert.ok(result!.warning?.includes("7.0"));
});

test("selectSchemaVersion returns null when no schemas", () => {
  const result = selectSchemaVersion(v74, []);
  assert.equal(result, null);
});

test("versionToFolderName formats correctly", () => {
  assert.equal(versionToFolderName(v74), "7.4");
});
