# Constitution - MCP FortiGate

## Project Identity
**Name:** mcp-fortigate  
**Purpose:** A Model Context Protocol (MCP) server that exposes FortiOS Configuration API capabilities to AI agents, enabling natural language management of FortiGate firewalls.

## Core Principles

### 1. API-First Design
- All operations map directly to FortiOS CMDB API endpoints
- Preserve FortiOS naming conventions and hierarchy
- Support FortiOS 7.4.9 as baseline version

### 2. Security by Default
- Never hardcode credentials
- Support API token authentication (FortiOS standard)
- Validate all inputs against FortiOS schema before sending
- Use HTTPS only for connections

### 3. Modular Architecture
- One MCP tool per FortiOS module (firewall, system, vpn, etc.)
- Lazy loading of API schemas to minimize startup time
- Pluggable authentication handlers

### 4. Developer Experience
- Clear error messages with FortiOS error context
- Input validation with helpful suggestions
- Consistent naming: use FortiOS original tag names (e.g., `firewall.policy`)

## Technology Stack
- **Runtime:** Node.js 18+ (for MCP SDK compatibility)
- **Language:** TypeScript
- **MCP SDK:** @modelcontextprotocol/sdk
- **HTTP Client:** axios or native fetch with timeout/retry
- **Schema Validation:** zod (for runtime) + JSON Schema (from Swagger)

## Coding Standards
- TypeScript strict mode enabled
- All API endpoints typed from Swagger schemas
- Functional error handling (Result/Either pattern preferred)
- Comprehensive JSDoc on all public methods

## Constraints
- Must handle FortiOS session timeouts gracefully
- Must support paginated responses
- Must validate IPv4/IPv6/CIDR inputs where applicable
- Maximum request timeout: 30 seconds

## Project Structure
```
src/
  client/          # FortiOS HTTP client
  tools/           # MCP tool definitions
  schemas/         # Parsed Swagger schemas
  auth/            # Authentication handlers
  utils/           # Helpers (validation, formatting)
types/             # TypeScript definitions
```
