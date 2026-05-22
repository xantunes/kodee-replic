/**
 * Mock FortiOS API Server for integration testing
 */

import { createServer, Server, IncomingMessage, ServerResponse } from "http";

export interface MockFortiOS {
  server: Server;
  port: number;
  url: string;
  requests: Array<{ method: string; path: string; body?: unknown }>;
  reset(): void;
  setResponse(path: string, method: string, data: unknown): void;
  setStatusCode(path: string, method: string, code: number): void;
}

export function startMockFortiOS(port = 0): Promise<MockFortiOS> {
  const requests: MockFortiOS["requests"] = [];
  const responses = new Map<string, unknown>();
  const statusCodes = new Map<string, number>();

  const server = createServer((req: IncomingMessage, res: ServerResponse) => {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", () => {
      const url = new URL(req.url || "/", `http://localhost:${port}`);
      const path = url.pathname;
      const method = req.method || "GET";
      const key = `${method}:${path}`;

      requests.push({
        method,
        path,
        body: body ? JSON.parse(body) : undefined,
      });

      // Check auth token
      const token = url.searchParams.get("access_token");
      if (!token && path !== "/api/v2/cmdb/system/status") {
        res.statusCode = 401;
        res.end(JSON.stringify({ error: 1, detail: "Invalid API token" }));
        return;
      }

      const statusCode = statusCodes.get(key) || 200;
      const data = responses.get(key);

      res.statusCode = statusCode;
      res.setHeader("Content-Type", "application/json");

      if (statusCode >= 400) {
        res.end(JSON.stringify({ error: 1, detail: "API Error" }));
        return;
      }

      if (data !== undefined) {
        res.end(JSON.stringify(data));
      } else {
        // Default responses for common endpoints
        if (path === "/api/v2/cmdb/system/status") {
          res.end(JSON.stringify({
            version: "v7.4.9",
            hostname: "FGT-MOCK",
            model: "FortiGate-VM",
            uptime: "10 days, 5 hours",
          }));
        } else if (path === "/api/v2/cmdb/system/performance") {
          res.end(JSON.stringify({
            cpu: 15,
            mem: 42,
            disk: 30,
            session: 1250,
            session_setup_rate: 45,
          }));
        } else if (path === "/api/v2/cmdb/firewall/policy") {
          res.end(JSON.stringify({
            results: [
              { policyid: 1, name: "WAN-to-LAN", action: "accept", status: "enable", logtraffic: "all" },
              { policyid: 2, name: "LAN-to-WAN", action: "accept", status: "enable", logtraffic: "disable" },
            ],
          }));
        } else if (path === "/api/v2/cmdb/firewall/address") {
          res.end(JSON.stringify({
            results: [
              { name: "WEB_SERVER", subnet: "10.0.1.10 255.255.255.255" },
              { name: "DB_SERVER", subnet: "10.0.1.20 255.255.255.255" },
            ],
          }));
        } else if (path === "/api/v2/cmdb/system/interface") {
          res.end(JSON.stringify({
            results: [
              { name: "port1", ip: "192.168.1.99 255.255.255.0", status: "up", type: "physical" },
              { name: "port2", ip: "10.0.0.1 255.255.255.0", status: "up", type: "physical" },
            ],
          }));
        } else if (path === "/api/v2/cmdb/vpn.ipsec/phase1-interface") {
          res.end(JSON.stringify({
            results: [
              { name: "vpn-sp", status: "up", type: "static" },
            ],
          }));
        } else {
          res.end(JSON.stringify({ results: [] }));
        }
      }
    });
  });

  return new Promise((resolve) => {
    server.listen(port, () => {
      const actualPort = (server.address() as { port: number }).port;
      resolve({
        server,
        port: actualPort,
        url: `http://localhost:${actualPort}`,
        requests,
        reset() {
          requests.length = 0;
          responses.clear();
          statusCodes.clear();
        },
        setResponse(path: string, method: string, data: unknown) {
          responses.set(`${method}:${path}`, data);
        },
        setStatusCode(path: string, method: string, code: number) {
          statusCodes.set(`${method}:${path}`, code);
        },
      });
    });
  });
}

export function stopMockFortiOS(mock: MockFortiOS): Promise<void> {
  return new Promise((resolve) => {
    mock.server.close(() => resolve());
  });
}
