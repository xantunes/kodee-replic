import assert from "node:assert";
import test from "node:test";
import { FortiOSClient } from "../../src/client/fortios-client.js";
import {
  FortiOSAuthError,
  FortiOSConnectionError,
  FortiOSApiError,
} from "../../src/client/errors.js";

test("FortiOSClient constructs with config", () => {
  const client = new FortiOSClient({
    host: "https://192.168.1.1",
    apiToken: "test-token",
  });
  assert.ok(client);
});

