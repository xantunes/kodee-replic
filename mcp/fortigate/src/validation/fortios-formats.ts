import { z } from "zod";

/**
 * FortiOS-specific format validators
 * Extend Zod with network and hardware format validation
 */

const IPV4_REGEX =
  /^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$/;

const IPV6_REGEX =
  /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$|^(?:[0-9a-fA-F]{1,4}:)*:[0-9a-fA-F]{1,4}$/;

const CIDR_REGEX =
  /^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\/(?:3[0-2]|[12]?\d)$/;

const MAC_REGEX = /^([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}$/;

const UUID_REGEX =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$/;

export const ipv4 = () =>
  z.string().regex(IPV4_REGEX, {
    message: "Invalid IPv4 address. Expected format: x.x.x.x (e.g., 192.168.1.1)",
  });

export const ipv6 = () =>
  z.string().regex(IPV6_REGEX, {
    message: "Invalid IPv6 address",
  });

export const cidr = () =>
  z.string().regex(CIDR_REGEX, {
    message: "Invalid CIDR. Expected format: x.x.x.x/y (e.g., 10.0.0.0/24)",
  });

export const macAddress = () =>
  z.string().regex(MAC_REGEX, {
    message: "Invalid MAC address. Expected format: xx:xx:xx:xx:xx:xx",
  });

export const uuid = () =>
  z.string().regex(UUID_REGEX, {
    message: "Invalid UUID format",
  });

/**
 * Auto-detect FortiOS format from parameter name and apply validator
 */
export function fortiosString(name: string): z.ZodString {
  const lower = name.toLowerCase();

  if (lower.includes("uuid") || lower.includes("guid")) return uuid();
  if (lower.includes("mac") || lower === "macaddr") return macAddress();
  if (lower.includes("cidr") || lower.includes("subnet")) return cidr();
  if (lower.includes("ip6") || lower.includes("ipv6") || lower.includes("v6addr"))
    return ipv6();
  if (lower.includes("ip") || lower.includes("addr") || lower.includes("gateway"))
    return ipv4();

  return z.string();
}
