import assert from "node:assert";
import test from "node:test";

test("governance access control loads", async () => {
  const { isReadonly, isFrozen, getFreezeStatus } = await import(
    "../../src/governance/access-control.js"
  );
  assert.ok(typeof isReadonly === "function");
  assert.ok(typeof isFrozen === "function");
  assert.ok(typeof getFreezeStatus === "function");
});
