import assert from "node:assert";
import test from "node:test";
import { parseSchema, generateToolName, getResourceName } from "../../src/schemas/parser.js";
import { SwaggerSchema } from "../../src/schemas/loader.js";

const mockSchema: SwaggerSchema = {
  swagger: "2.0",
  info: { title: "Test API", description: "Test", version: "v1" },
  basePath: "/api/v2/cmdb",
  tags: [
    { name: "firewall.policy", description: "Firewall policies" },
  ],
  paths: {
    "/firewall/policy": {
      get: {
        tags: ["firewall.policy"],
        summary: "List policies",
        responses: { "200": { description: "OK" } },
      },
      post: {
        tags: ["firewall.policy"],
        summary: "Create policy",
        responses: { "200": { description: "OK" } },
      },
    },
    "/firewall/policy/{id}": {
      get: {
        tags: ["firewall.policy"],
        summary: "Get policy",
        responses: { "200": { description: "OK" } },
      },
    },
  },
};

test("parseSchema extracts tags and endpoints", () => {
  const parsed = parseSchema(mockSchema, "firewall");
  assert.equal(parsed.moduleName, "firewall");
  assert.equal(parsed.tags.length, 1);
  assert.equal(parsed.tags[0].tag, "firewall.policy");
  assert.equal(parsed.tags[0].endpoints.length, 3);
});

test("generateToolName creates valid names", () => {
  assert.equal(generateToolName("firewall", "policy"), "fortios_firewall_policy");
  assert.equal(generateToolName("system", "interface"), "fortios_system_interface");
});

test("getResourceName extracts resource from tag", () => {
  assert.equal(getResourceName("firewall.policy"), "policy");
  assert.equal(getResourceName("system.interface"), "interface");
});
