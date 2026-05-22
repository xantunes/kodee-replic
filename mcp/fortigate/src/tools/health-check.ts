import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { FortiOSClient } from "../client/fortios-client.js";

export const HEALTH_CHECK_TOOL_NAME = "fortios_health_check";

export function getHealthCheckTool(): Tool {
  return {
    name: HEALTH_CHECK_TOOL_NAME,
    description:
      "Check FortiGate connectivity and retrieve system status. " +
      "Returns version, hostname, model, and uptime.",
    inputSchema: {
      type: "object",
      properties: {},
    } as Tool["inputSchema"],
  };
}

export async function handleHealthCheck(
  _args: Record<string, unknown>,
  client: FortiOSClient
): Promise<unknown> {
  try {
    // FortiOS system status endpoint
    const response = (await client.monitorGet("/system/status")) as {
      version?: string;
      build?: number;
      results?: {
        hostname?: string;
        model?: string;
        model_name?: string;
        uptime?: string;
      };
    };

    const results = response.results || {};
    const hostname = results.hostname || "unknown";
    const model = results.model || results.model_name || "unknown";

    return {
      status: "connected",
      fortigate: {
        version: response.version || "unknown",
        hostname,
        model,
        uptime: results.uptime || "unknown",
        build: response.build ? String(response.build) : "unknown",
      },
      message: `Connected to ${hostname} (${model})`,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      status: "error",
      message: `Health check failed: ${message}`,
      suggestions: [
        "Verify FORTIOS_HOST is correct (use HTTPS)",
        "Check FORTIOS_API_TOKEN is valid",
        "Ensure FortiGate API access is enabled",
        "For self-signed certs: set FORTIOS_VERIFY_SSL=false",
      ],
    };
  }
}
