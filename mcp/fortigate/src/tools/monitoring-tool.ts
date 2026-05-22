import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { FortiOSClient } from "../client/fortios-client.js";

export const SYSTEM_PERF_TOOL_NAME = "fortios_system_perf";
export const INTERFACE_STATUS_TOOL_NAME = "fortios_interface_status";
export const VPN_STATUS_TOOL_NAME = "fortios_vpn_status";
export const TOP_SESSIONS_TOOL_NAME = "fortios_top_sessions";

export function getSystemPerfTool(): Tool {
  return {
    name: SYSTEM_PERF_TOOL_NAME,
    description: "Get FortiGate system performance metrics: CPU, memory, disk, uptime, session count.",
    inputSchema: { type: "object", properties: {} } as Tool["inputSchema"],
  };
}

export function getInterfaceStatusTool(): Tool {
  return {
    name: INTERFACE_STATUS_TOOL_NAME,
    description: "Get status of all network interfaces: up/down, IP, speed, RX/TX bytes, errors.",
    inputSchema: { type: "object", properties: {} } as Tool["inputSchema"],
  };
}

export function getVpnStatusTool(): Tool {
  return {
    name: VPN_STATUS_TOOL_NAME,
    description: "Get VPN tunnel status: IPsec phase1/phase2 and SSL VPN users.",
    inputSchema: { type: "object", properties: {} } as Tool["inputSchema"],
  };
}

export function getTopSessionsTool(): Tool {
  return {
    name: TOP_SESSIONS_TOOL_NAME,
    description: "Get top active sessions by bandwidth usage.",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "number", description: "Number of top sessions (default: 20)" },
      },
    } as Tool["inputSchema"],
  };
}

export async function handleSystemPerf(client: FortiOSClient): Promise<unknown> {
  try {
    const status = (await client.get("/system/status")) as Record<string, unknown>;
    const perf = (await client.get("/system/performance")) as Record<string, unknown>;

    return {
      status: "success",
      hostname: status.hostname,
      version: status.version,
      model: status.model,
      uptime: status.uptime,
      cpu: perf.cpu,
      memory: perf.mem,
      disk: perf.disk,
      sessions: perf.session,
      session_setup_rate: perf.session_setup_rate,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { status: "error", message };
  }
}

export async function handleInterfaceStatus(client: FortiOSClient): Promise<unknown> {
  try {
    const resp = (await client.get("/system/interface", { params: { count: 1 } })) as {
      results?: Array<Record<string, unknown>>;
    };

    const interfaces = (resp.results || []).map((iface) => ({
      name: iface.name,
      alias: iface.alias,
      type: iface.type,
      status: iface.status,
      speed: iface.speed,
      ip: iface.ip,
      mac: iface.macaddr,
      rx_bytes: iface.rx_bytes,
      tx_bytes: iface.tx_bytes,
      rx_errors: iface.rx_errors,
      tx_errors: iface.tx_errors,
    }));

    return { status: "success", count: interfaces.length, interfaces };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { status: "error", message };
  }
}

export async function handleVpnStatus(client: FortiOSClient): Promise<unknown> {
  try {
    const ipsec = (await client.get("/vpn.ipsec/phase1-interface", { params: { count: 1 } })) as {
      results?: Array<Record<string, unknown>>;
    };

    const ssl = (await client.get("/vpn.ssl/settings")) as Record<string, unknown>;

    const tunnels = (ipsec.results || []).map((t) => ({
      name: t.name,
      type: t.type,
      interface: t.interface,
      status: t.status,
    }));

    return {
      status: "success",
      ipsec_tunnels: tunnels.length,
      tunnels,
      ssl_vpn: {
        status: ssl.status,
        port: ssl.port,
      },
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { status: "error", message };
  }
}

export async function handleTopSessions(
  args: Record<string, unknown>,
  client: FortiOSClient
): Promise<unknown> {
  const limit = (args.limit as number) || 20;

  try {
    const resp = (await client.get("/firewall/session", { params: { count: 1, limit } })) as {
      results?: Array<Record<string, unknown>>;
    };

    const sessions = (resp.results || []).map((s) => ({
      src_ip: s.src_ip,
      src_port: s.src_port,
      dst_ip: s.dst_ip,
      dst_port: s.dst_port,
      protocol: s.protocol,
      policy_id: s.policy_id,
      duration: s.duration,
      bytes: s.bytes,
    }));

    return { status: "success", count: sessions.length, sessions };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { status: "error", message };
  }
}
