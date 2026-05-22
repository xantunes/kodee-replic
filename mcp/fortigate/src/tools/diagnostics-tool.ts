import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { FortiOSClient } from "../client/fortios-client.js";

export const PING_TOOL_NAME = "fortios_ping";
export const TRACEROUTE_TOOL_NAME = "fortios_traceroute";
export const PACKET_CAPTURE_TOOL_NAME = "fortios_packet_capture";

export function getPingTool(): Tool {
  return {
    name: PING_TOOL_NAME,
    description: "Execute ping from FortiGate to a target IP or hostname.",
    inputSchema: {
      type: "object",
      properties: {
        target: { type: "string", description: "IP or hostname to ping" },
        count: { type: "number", description: "Number of pings (default: 4)" },
        source_interface: { type: "string", description: "Source interface (optional)" },
      },
      required: ["target"],
    } as Tool["inputSchema"],
  };
}

export function getTracerouteTool(): Tool {
  return {
    name: TRACEROUTE_TOOL_NAME,
    description: "Execute traceroute from FortiGate to a target IP or hostname.",
    inputSchema: {
      type: "object",
      properties: {
        target: { type: "string", description: "IP or hostname" },
        source_interface: { type: "string", description: "Source interface (optional)" },
      },
      required: ["target"],
    } as Tool["inputSchema"],
  };
}

export function getPacketCaptureTool(): Tool {
  return {
    name: PACKET_CAPTURE_TOOL_NAME,
    description:
      "Capture packets on a FortiGate interface. " +
      "Returns packet summary (not raw bytes). Max duration: 60 seconds.",
    inputSchema: {
      type: "object",
      properties: {
        interface: { type: "string", description: "Interface to capture on (e.g., port1)" },
        filter: { type: "string", description: "Capture filter (e.g., 'host 10.0.0.5')" },
        duration_seconds: { type: "number", description: "Duration 1-60 (default: 10)" },
      },
      required: ["interface"],
    } as Tool["inputSchema"],
  };
}

export async function handlePing(
  args: Record<string, unknown>,
  client: FortiOSClient
): Promise<unknown> {
  const target = args.target as string;
  const count = (args.count as number) || 4;
  const source = (args.source_interface as string) || "";

  try {
    // FortiOS API v2 has a diagnostic endpoint for ping
    const result = (await client.post("/system/ping", {
      data: {
        "destination": target,
        "count": count,
        "interface": source || undefined,
      },
    })) as Record<string, unknown>;

    return {
      status: "success",
      target,
      count,
      source_interface: source || "auto",
      result,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    // Fallback: try exec ping via CLI API if available
    return {
      status: "error",
      message: `Ping failed: ${message}`,
      note: "Ensure FortiOS API allows diagnostic commands",
    };
  }
}

export async function handleTraceroute(
  args: Record<string, unknown>,
  client: FortiOSClient
): Promise<unknown> {
  const target = args.target as string;
  const source = (args.source_interface as string) || "";

  try {
    const result = (await client.post("/system/traceroute", {
      data: {
        "destination": target,
        "interface": source || undefined,
      },
    })) as Record<string, unknown>;

    return {
      status: "success",
      target,
      source_interface: source || "auto",
      result,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      status: "error",
      message: `Traceroute failed: ${message}`,
    };
  }
}

export async function handlePacketCapture(
  args: Record<string, unknown>,
  client: FortiOSClient
): Promise<unknown> {
  const iface = args.interface as string;
  const filter = (args.filter as string) || "";
  const duration = Math.min(Math.max((args.duration_seconds as number) || 10, 1), 60);

  try {
    // Start capture
    await client.post("/system/packet-capture", {
      data: {
        "interface": iface,
        "filter": filter,
        "max-packet-count": 100,
      },
    });

    // Wait for capture duration
    await new Promise((resolve) => setTimeout(resolve, duration * 1000));

    // Stop and get results
    const captureResult = (await client.get("/system/packet-capture")) as {
      results?: Array<Record<string, unknown>>;
    };

    const packets = (captureResult.results || []).map((p) => ({
      timestamp: p.timestamp,
      src_ip: p.src_ip,
      dst_ip: p.dst_ip,
      protocol: p.protocol,
      src_port: p.src_port,
      dst_port: p.dst_port,
      length: p.length,
    }));

    return {
      status: "success",
      interface: iface,
      filter: filter || "none",
      duration_seconds: duration,
      packets_captured: packets.length,
      packets,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      status: "error",
      message: `Packet capture failed: ${message}`,
      note: "Ensure FortiOS API allows packet capture and interface exists",
    };
  }
}
