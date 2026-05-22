#!/usr/bin/env node
/**
 * MCP FortiGate Server
 * Model Context Protocol server for FortiOS Configuration API
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { FortiOSClient } from "./client/fortios-client.js";
import { loadAllSchemas, getModuleName } from "./schemas/loader.js";
import { parseSchema } from "./schemas/parser.js";
import { globalSchemaCache } from "./schemas/cache.js";
import {
  detectFortiOSVersion,
  parseVersion,
  versionToFolderName,
} from "./schemas/version-detector.js";
import {
  discoverAvailableVersions,
  selectSchemaVersion,
  getSchemaDir,
} from "./schemas/version-selector.js";
import { discoverApiEndpoints, buildDynamicSchema } from "./schemas/runtime-discovery.js";
import { generateToolDefinitions, handleToolCall, registerToolHandler } from "./tools/generator.js";
import { getRollbackTool, handleRollback, ROLLBACK_TOOL_NAME } from "./tools/rollback-tool.js";
import {
  getHealthCheckTool,
  handleHealthCheck,
  HEALTH_CHECK_TOOL_NAME,
} from "./tools/health-check.js";
import {
  getSearchTool,
  handleSearch,
  SEARCH_TOOL_NAME,
} from "./tools/search-tool.js";
import { getAuditTool, handleAudit, AUDIT_TOOL_NAME } from "./tools/audit-tool.js";
import { logAudit, hashToken } from "./audit/logger.js";
import { assertCanMutate } from "./governance/access-control.js";
import { getDiffTool, handleDiff, DIFF_TOOL_NAME } from "./tools/diff-tool.js";
import {
  getDependencyTool,
  handleDependencies,
  DEPENDENCY_TOOL_NAME,
} from "./tools/dependency-tool.js";
import {
  getAnalyzerTool,
  handleAnalyze,
  ANALYZER_TOOL_NAME,
} from "./tools/analyzer-tool.js";
import {
  getBulkCreateTool,
  getBulkDeleteTool,
  handleBulkCreate,
  handleBulkDelete,
  BULK_CREATE_TOOL_NAME,
  BULK_DELETE_TOOL_NAME,
} from "./tools/bulk-tool.js";
import {
  getSystemPerfTool,
  getInterfaceStatusTool,
  getVpnStatusTool,
  getTopSessionsTool,
  handleSystemPerf,
  handleInterfaceStatus,
  handleVpnStatus,
  handleTopSessions,
  SYSTEM_PERF_TOOL_NAME,
  INTERFACE_STATUS_TOOL_NAME,
  VPN_STATUS_TOOL_NAME,
  TOP_SESSIONS_TOOL_NAME,
} from "./tools/monitoring-tool.js";
import {
  getTemplateApplyTool,
  getTemplateListTool,
  handleTemplateApply,
  handleTemplateList,
  TEMPLATE_APPLY_TOOL_NAME,
  TEMPLATE_LIST_TOOL_NAME,
} from "./tools/template-tool.js";
import {
  getPingTool,
  getTracerouteTool,
  getPacketCaptureTool,
  handlePing,
  handleTraceroute,
  handlePacketCapture,
  PING_TOOL_NAME,
  TRACEROUTE_TOOL_NAME,
  PACKET_CAPTURE_TOOL_NAME,
} from "./tools/diagnostics-tool.js";
import {
  getFreezeTool,
  getUnfreezeTool,
  getFreezeStatusTool,
  getPendingChangesTool,
  getApproveChangeTool,
  getGovernanceStatusTool,
  handleFreeze,
  handleUnfreeze,
  handleFreezeStatus,
  handlePendingChanges,
  handleApproveChange,
  handleGovernanceStatus,
  FREEZE_TOOL_NAME,
  UNFREEZE_TOOL_NAME,
  FREEZE_STATUS_TOOL_NAME,
  PENDING_CHANGES_TOOL_NAME,
  APPROVE_CHANGE_TOOL_NAME,
  GOVERNANCE_STATUS_TOOL_NAME,
} from "./tools/governance-tool.js";
import { resolve } from "path";
import { fileURLToPath } from "url";

// Environment configuration
const FORTIOS_HOST = process.env.FORTIOS_HOST;
const FORTIOS_API_TOKEN = process.env.FORTIOS_API_TOKEN;
const FORTIOS_DRY_RUN = process.env.FORTIOS_DRY_RUN === "true";

if (!FORTIOS_HOST) {
  console.error("Error: FORTIOS_HOST environment variable is required");
  process.exit(1);
}

if (!FORTIOS_API_TOKEN) {
  console.error("Error: FORTIOS_API_TOKEN environment variable is required");
  process.exit(1);
}

// Initialize FortiOS client
const client = new FortiOSClient({
  host: FORTIOS_HOST,
  apiToken: FORTIOS_API_TOKEN,
  verifySsl: process.env.FORTIOS_VERIFY_SSL !== "false",
});

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const SCHEMAS_BASE_DIR = resolve(__dirname, "../schemas");

// Version selection logic
let schemaDir = SCHEMAS_BASE_DIR;
let versionWarning: string | undefined;

const FORTIOS_VERSION_OVERRIDE = process.env.FORTIOS_VERSION;

if (FORTIOS_VERSION_OVERRIDE) {
  const overrideVersion = parseVersion(FORTIOS_VERSION_OVERRIDE);
  if (overrideVersion) {
    schemaDir = getSchemaDir(SCHEMAS_BASE_DIR, overrideVersion);
    console.error(`MCP FortiGate: Using manually specified version ${versionToFolderName(overrideVersion)}`);
  } else {
    console.error(`MCP FortiGate: Warning: Invalid FORTIOS_VERSION="${FORTIOS_VERSION_OVERRIDE}". Using default.`);
  }
} else {
  try {
    const detectedVersion = await Promise.race([
      detectFortiOSVersion(client),
      new Promise<null>((_, reject) =>
        setTimeout(() => reject(new Error("Timeout")), 5000)
      ),
    ]);
    if (detectedVersion) {
      const availableVersions = discoverAvailableVersions(SCHEMAS_BASE_DIR);
      const selection = selectSchemaVersion(detectedVersion, availableVersions);

      if (selection) {
        schemaDir = getSchemaDir(SCHEMAS_BASE_DIR, selection.selected);
        versionWarning = selection.warning;
        console.error(
          `MCP FortiGate: Detected FortiOS ${detectedVersion.raw}, using schemas ${versionToFolderName(selection.selected)}`
        );
        if (versionWarning) {
          console.error(`MCP FortiGate: Warning: ${versionWarning}`);
        }
      } else {
        console.error(
          `MCP FortiGate: Warning: No local schemas found for FortiOS ${detectedVersion.raw}. Will attempt runtime discovery.`
        );
      }
    } else {
      console.error(`MCP FortiGate: Could not detect FortiOS version. Using default schemas.`);
    }
  } catch {
    console.error(`MCP FortiGate: Could not detect FortiOS version. Using default schemas.`);
  }
}

// Load schemas (local or runtime discovery)
const allTools: Tool[] = [];
let schemaFiles: import("./schemas/loader.js").SwaggerSchema[] = [];

// Fallback: if schemaDir is base dir, try to find any version subfolder
if (schemaDir === SCHEMAS_BASE_DIR) {
  const available = discoverAvailableVersions(SCHEMAS_BASE_DIR);
  if (available.length > 0) {
    const fallbackVersion = available[available.length - 1]; // Use newest
    schemaDir = getSchemaDir(SCHEMAS_BASE_DIR, fallbackVersion);
    console.error(`MCP FortiGate: Using fallback schemas ${versionToFolderName(fallbackVersion)}`);
  }
}

try {
  schemaFiles = loadAllSchemas(schemaDir);
} catch {
  schemaFiles = [];
}

if (schemaFiles.length === 0) {
  console.error(`MCP FortiGate: No local schemas found in ${schemaDir}. Attempting runtime discovery...`);
  const commonPaths = [
    "/firewall/policy", "/firewall/address", "/system/interface",
    "/router/static", "/vpn.ipsec/phase1-interface", "/user/local",
  ];
  try {
    const discovered = await Promise.race([
      discoverApiEndpoints(client, commonPaths),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error("Timeout")), 8000)
      ),
    ]);
    if (discovered.length > 0) {
      const dynamicSchema = buildDynamicSchema(discovered, "cmdb");
      schemaFiles = [dynamicSchema];
      console.error(`MCP FortiGate: Runtime discovery found ${discovered.length} endpoints`);
    } else {
      console.error(`MCP FortiGate: Runtime discovery failed. Server will have limited functionality.`);
    }
  } catch {
    console.error(`MCP FortiGate: Runtime discovery failed. Server will have limited functionality.`);
  }
}

for (const schema of schemaFiles) {
  const moduleName = getModuleName(schema.info.title || "unknown");
  const parsed = parseSchema(schema, moduleName);
  globalSchemaCache.set(moduleName, parsed);

  const tools = generateToolDefinitions(parsed, client, FORTIOS_DRY_RUN);
  allTools.push(...tools);
}

// Register special tools
allTools.push(getRollbackTool());
registerToolHandler(ROLLBACK_TOOL_NAME, (args, client, dryRun) =>
  handleRollback(args, client, dryRun)
);

allTools.push(getHealthCheckTool());
registerToolHandler(HEALTH_CHECK_TOOL_NAME, (args, client, _dryRun) =>
  handleHealthCheck(args, client)
);

allTools.push(getSearchTool());
registerToolHandler(SEARCH_TOOL_NAME, (args, client, _dryRun) =>
  handleSearch(args, client)
);

allTools.push(getAuditTool());
allTools.push(getDiffTool());
allTools.push(getDependencyTool());
allTools.push(getAnalyzerTool());
allTools.push(getBulkCreateTool());
allTools.push(getBulkDeleteTool());
allTools.push(getSystemPerfTool());
allTools.push(getInterfaceStatusTool());
allTools.push(getVpnStatusTool());
allTools.push(getTopSessionsTool());
allTools.push(getTemplateApplyTool());
allTools.push(getTemplateListTool());
allTools.push(getPingTool());
allTools.push(getTracerouteTool());
allTools.push(getPacketCaptureTool());
allTools.push(getFreezeTool());
allTools.push(getUnfreezeTool());
allTools.push(getFreezeStatusTool());
allTools.push(getPendingChangesTool());
allTools.push(getApproveChangeTool());
allTools.push(getGovernanceStatusTool());

console.error(`MCP FortiGate: Loaded ${schemaFiles.length} modules, ${allTools.length} tools`);

// Create MCP server
const server = new Server(
  {
    name: "mcp-fortigate",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Register tool list handler
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: allTools };
});

// Register tool call handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  const tool = allTools.find((t) => t.name === name);
  if (!tool) {
    return {
      content: [
        {
          type: "text",
          text: `Error: Unknown tool "${name}"`,
        },
      ],
      isError: true,
    };
  }

  const startTime = Date.now();
  let errorMessage: string | undefined;

  try {
    let result: unknown;

    // ─── Governance Check for Mutating Operations ─────────────────────
    const operation = (args || {}).operation as string | undefined;
    const readOnlySpecialTools = [
      AUDIT_TOOL_NAME, DIFF_TOOL_NAME, DEPENDENCY_TOOL_NAME, ANALYZER_TOOL_NAME,
      SYSTEM_PERF_TOOL_NAME, INTERFACE_STATUS_TOOL_NAME, VPN_STATUS_TOOL_NAME,
      TOP_SESSIONS_TOOL_NAME, TEMPLATE_LIST_TOOL_NAME, PING_TOOL_NAME,
      TRACEROUTE_TOOL_NAME, PACKET_CAPTURE_TOOL_NAME, FREEZE_STATUS_TOOL_NAME,
      PENDING_CHANGES_TOOL_NAME, GOVERNANCE_STATUS_TOOL_NAME,
      HEALTH_CHECK_TOOL_NAME, SEARCH_TOOL_NAME,
    ];
    const alwaysMutatingTools = [
      BULK_CREATE_TOOL_NAME, BULK_DELETE_TOOL_NAME,
      TEMPLATE_APPLY_TOOL_NAME, ROLLBACK_TOOL_NAME,
      FREEZE_TOOL_NAME, UNFREEZE_TOOL_NAME, APPROVE_CHANGE_TOOL_NAME,
    ];

    let isMutating = false;
    if (alwaysMutatingTools.includes(name)) {
      isMutating = true;
    } else if (readOnlySpecialTools.includes(name)) {
      isMutating = false;
    } else if (name.startsWith("fortios_") && operation) {
      // Generated CRUD tools: list/get are reads, create/update/delete are mutations
      isMutating = !["list", "get"].includes(operation);
    } else if (name.startsWith("fortios_")) {
      // Fallback: any other fortios_ tool without operation is considered mutating
      isMutating = true;
    }

    const changeToken = (args || {}).change_token as string | undefined;
    const approverToken = (args || {}).approver_token as string | undefined;

    if (isMutating && !FORTIOS_DRY_RUN) {
      assertCanMutate(name, changeToken, approverToken);
    }

    if (name === AUDIT_TOOL_NAME) {
      result = await handleAudit(args || {});
    } else if (name === DIFF_TOOL_NAME) {
      result = await handleDiff(args || {}, client);
    } else if (name === DEPENDENCY_TOOL_NAME) {
      result = await handleDependencies(args || {}, client);
    } else if (name === ANALYZER_TOOL_NAME) {
      result = await handleAnalyze(args || {}, client);
    } else if (name === BULK_CREATE_TOOL_NAME) {
      result = await handleBulkCreate(args || {}, client, FORTIOS_DRY_RUN);
    } else if (name === BULK_DELETE_TOOL_NAME) {
      result = await handleBulkDelete(args || {}, client, FORTIOS_DRY_RUN);
    } else if (name === SYSTEM_PERF_TOOL_NAME) {
      result = await handleSystemPerf(client);
    } else if (name === INTERFACE_STATUS_TOOL_NAME) {
      result = await handleInterfaceStatus(client);
    } else if (name === VPN_STATUS_TOOL_NAME) {
      result = await handleVpnStatus(client);
    } else if (name === TOP_SESSIONS_TOOL_NAME) {
      result = await handleTopSessions(args || {}, client);
    } else if (name === TEMPLATE_APPLY_TOOL_NAME) {
      result = await handleTemplateApply(args || {}, client, FORTIOS_DRY_RUN);
    } else if (name === TEMPLATE_LIST_TOOL_NAME) {
      result = await handleTemplateList();
    } else if (name === PING_TOOL_NAME) {
      result = await handlePing(args || {}, client);
    } else if (name === TRACEROUTE_TOOL_NAME) {
      result = await handleTraceroute(args || {}, client);
    } else if (name === PACKET_CAPTURE_TOOL_NAME) {
      result = await handlePacketCapture(args || {}, client);
    } else if (name === FREEZE_TOOL_NAME) {
      result = await handleFreeze(args || {});
    } else if (name === UNFREEZE_TOOL_NAME) {
      result = await handleUnfreeze(args || {});
    } else if (name === FREEZE_STATUS_TOOL_NAME) {
      result = await handleFreezeStatus();
    } else if (name === PENDING_CHANGES_TOOL_NAME) {
      result = await handlePendingChanges();
    } else if (name === APPROVE_CHANGE_TOOL_NAME) {
      result = await handleApproveChange(args || {});
    } else if (name === GOVERNANCE_STATUS_TOOL_NAME) {
      result = await handleGovernanceStatus();
    } else if (name === ROLLBACK_TOOL_NAME) {
      result = await handleRollback(args || {}, client, FORTIOS_DRY_RUN);
    } else if (name === HEALTH_CHECK_TOOL_NAME) {
      result = await handleHealthCheck(args || {}, client);
    } else if (name === SEARCH_TOOL_NAME) {
      result = await handleSearch(args || {}, client);
    } else {
      result = await handleToolCall(name, args, client, FORTIOS_DRY_RUN);
    }

    // Log audit entry
    logAudit({
      timestamp: new Date().toISOString(),
      tool: name,
      operation: (args || {}).operation as string || "call",
      args: (args || {}) as Record<string, unknown>,
      status: "success",
      duration_ms: Date.now() - startTime,
      token_hash: hashToken(FORTIOS_API_TOKEN),
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : String(error);

    // Log failed operation
    logAudit({
      timestamp: new Date().toISOString(),
      tool: name,
      operation: (args || {}).operation as string || "call",
      args: (args || {}) as Record<string, unknown>,
      status: "error",
      error_message: errorMessage,
      duration_ms: Date.now() - startTime,
      token_hash: hashToken(FORTIOS_API_TOKEN),
    });

    return {
      content: [
        {
          type: "text",
          text: `Error: ${errorMessage}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);

console.error("MCP FortiGate server running on stdio");
