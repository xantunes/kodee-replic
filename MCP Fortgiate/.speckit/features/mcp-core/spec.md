# Feature Specification: MCP FortiGate Core

## Overview
Create a Model Context Protocol (MCP) server that exposes FortiOS 7.4.9 Configuration API capabilities to AI agents. The MCP server will allow AI assistants to manage FortiGate firewalls through natural language by translating requests into REST API calls.

## Existing Assets Analysis
The project contains **72 Swagger 2.0 JSON files** covering FortiOS CMDB API modules:
- firewall, system, vpn, user, router, switch-controller
- security profiles (antivirus, ips, webfilter, dnsfilter, application)
- network (interface, sdwan, router, switch)
- objects (address, service, vip, ippool)
- And 60+ additional modules

Each file follows Swagger 2.0 spec with:
- Base path: `/api/v2/cmdb`
- Authentication: API Key query param (`access_token`)
- Tags per endpoint group (e.g., `firewall.policy`, `system.interface`)

## User Stories

### US-001: Natural Language Firewall Management
**As an** AI assistant user  
**I want to** say "block IP 10.0.0.5 on the WAN interface"  
**So that** the firewall rule is created without manual API calls  

**Acceptance Criteria:**
- MCP tool accepts natural language intent
- Maps to correct FortiOS endpoint (`firewall/policy`)
- Validates inputs against FortiOS schema
- Returns operation result with rule ID

### US-002: Configuration Retrieval
**As an** administrator  
**I want to** ask "show me all firewall policies"  
**So that** I can review configurations conversationally  

**Acceptance Criteria:**
- Supports GET operations on all CMDB endpoints
- Returns formatted, readable output
- Supports filtering by name, ID, or attributes

### US-003: Safe Configuration Changes
**As an** administrator  
**I want to** preview changes before applying  
**So that** I don't break production firewall rules  

**Acceptance Criteria:**
- Dry-run mode for all mutating operations
- Input validation before API call
- Confirmation prompt for destructive operations

### US-004: Multi-Module Operations
**As an** administrator  **I want to** manage addresses, services, and policies in one conversation  
**So that** I don't switch between tools  

**Acceptance Criteria:**
- All 72 FortiOS modules accessible
- Consistent tool interface across modules
- Cross-reference validation (e.g., policy references existing address)

## Functional Requirements

### FR-001: MCP Server Initialization
The server MUST initialize with:
- FortiGate host URL (configurable)
- API token (from environment variable `FORTIOS_API_TOKEN`)
- Optional: SSL verification toggle (default: true)

### FR-002: Dynamic Tool Registration
The server MUST dynamically generate MCP tools from Swagger schemas:
- Parse all 72 JSON files at startup
- Create one tool per Swagger `tag`
- Tool name format: `fortios_{module}_{submodule}` (e.g., `fortios_firewall_policy`)

### FR-003: CRUD Operations
Each tool MUST support:
- `list` - GET all objects (with pagination)
- `get` - GET single object by ID/name
- `create` - POST new object
- `update` - PUT existing object
- `delete` - DELETE object

### FR-004: Schema Validation
All inputs MUST be validated:
- Required fields from Swagger `required` array
- Type checking (string, integer, boolean, array)
- FortiOS-specific formats (ipv4, ipv6, mac, uuid)

### FR-005: Error Handling
Errors MUST be handled gracefully:
- FortiOS 4xx errors: return user-friendly message with FortiOS error detail
- Connection errors: retry with exponential backoff (max 3 attempts)
- Timeout errors: clear message suggesting to check connectivity

## Success Criteria

### SC-001: Coverage
- [ ] All 72 FortiOS modules exposed as MCP tools
- [ ] At least 90% of Swagger endpoints mapped

### SC-002: Reliability
- [ ] Zero unhandled exceptions in normal operation
- [ ] All API errors surfaced to user with context

### SC-003: Usability
- [ ] Natural language operations work without memorizing API names
- [ ] Response formatting is human-readable

### SC-004: Performance
- [ ] Server startup < 5 seconds (with lazy schema loading)
- [ ] API response time < 30 seconds (FortiOS-dependent)

## Edge Cases

### EC-001: FortiOS Version Mismatch
If connected FortiOS version differs from 7.4.9, warn user but attempt operation.

### EC-002: Large Configurations
For endpoints returning >1000 objects, implement pagination and streaming.

### EC-003: Session Expiry
Handle FortiOS session timeout by re-authenticating transparently.

### EC-004: Concurrent Modifications
If object changed between read and write, surface conflict to user.

## Dependencies
- Node.js 18+ runtime
- @modelcontextprotocol/sdk
- Access to FortiOS 7.4.9 device or emulator for testing

## Out of Scope
- Real-time log streaming (syslog integration)
- Firmware management (upgrade/downgrade)
- HA cluster management
- FortiManager integration
