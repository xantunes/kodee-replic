import assert from "node:assert";
import test from "node:test";
import { FortiOSClient } from "../../src/client/fortios-client.js";
import { startMockFortiOS, stopMockFortiOS, MockFortiOS } from "../mocks/fortios-server.js";
import { handleHealthCheck } from "../../src/tools/health-check.js";
import { handleSearch } from "../../src/tools/search-tool.js";
import { handleSystemPerf } from "../../src/tools/monitoring-tool.js";
import { handleInterfaceStatus } from "../../src/tools/monitoring-tool.js";

let mock: MockFortiOS;
let client: FortiOSClient;

test("setup mock server", async () => {
  mock = await startMockFortiOS();
  client = new FortiOSClient({
    host: mock.url,
    apiToken: "test-token",
    verifySsl: false,
  });
  assert.ok(mock.port > 0);
});

test("health check returns system info", async () => {
  const result = (await handleHealthCheck({}, client)) as {
    status: string;
    fortigate: { hostname: string };
  };
  assert.equal(result.status, "connected");
  assert.equal(result.fortigate.hostname, "FGT-MOCK");
});

test("search finds firewall policies", async () => {
  const result = (await handleSearch({ query: "WAN" }, client)) as {
    status: string;
    totalMatches: number;
  };
  assert.equal(result.status, "success");
  assert.ok(result.totalMatches > 0);
});

test("system perf returns metrics", async () => {
  const result = (await handleSystemPerf(client)) as {
    status: string;
    cpu: number;
  };
  assert.equal(result.status, "success");
  assert.equal(result.cpu, 15);
});

test("interface status returns interfaces", async () => {
  const result = (await handleInterfaceStatus(client)) as {
    status: string;
    count: number;
  };
  assert.equal(result.status, "success");
  assert.equal(result.count, 2);
});

test("client handles 401 error", async () => {
  mock.setStatusCode("/api/v2/cmdb/firewall/policy", "GET", 401);
  try {
    await client.get("/firewall/policy");
    assert.fail("Should have thrown");
  } catch (error) {
    assert.ok(error instanceof Error);
  }
  mock.reset();
});

test("teardown mock server", async () => {
  await stopMockFortiOS(mock);
});
