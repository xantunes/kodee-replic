/**
 * E2E Test Runner
 */

import { run } from "node:test";
import { spec } from "node:test/reporters";
import { readdirSync } from "fs";
import { resolve } from "path";

const files = readdirSync("tests/e2e")
  .filter((f) => f.endsWith(".test.ts"))
  .map((f) => resolve("tests/e2e", f));

run({ files, reporter: spec })
  .then((result) => {
    process.exit(result.failure ? 1 : 0);
  })
  .catch(() => process.exit(1));
