# MCP FortiGate

Model Context Protocol (MCP) server for FortiOS Configuration API. Enables AI assistants to manage FortiGate firewalls through natural language.

## Features

### Core Operations
- 🔥 **78 FortiOS modules** exposed as MCP tools (600+ tools)
- 🔒 **Secure API token authentication**
- 📝 **Dry-run mode** for safe configuration preview
- 🏥 **Health check** tool — verify connectivity instantly
- 🔍 **Global search** — find objects across all modules
- 📄 **Auto-pagination** — fetch thousands of items automatically
- ✅ **Input validation** — validates IPs, MACs, CIDRs before sending
- 📋 **Markdown formatting** — readable tables and key-value output
- 🔄 **Rollback support** — undo last change with one command

### Governance (Critical Environments)
- 🔐 **Readonly by default** — mutations require explicit change token
- 👥 **Two-person rule** — approver token required for mutations
- 🧊 **Emergency freeze** — instantly block all changes
- ⏰ **Change windows** — only allow mutations during maintenance windows

### Automation & Analysis
- 📊 **Bulk operations** — create/delete multiple objects at once
- 📈 **Real-time monitoring** — CPU, memory, interfaces, VPN, sessions
- 📦 **Config templates** — deploy VPN, DMZ, Guest WiFi in one call
- 🔧 **Diagnostics** — ping, traceroute, packet capture
- 📝 **Audit log** — persistent record of all operations
- 🔍 **Config diff** — compare objects or backups
- 🔗 **Dependency graph** — find orphans and usage
- 🛡️ **Config analyzer** — detect security issues

## Quick Start

### 1. Install

```bash
cd mcp-fortigate
npm install
npm run build
```

### 2. Configure Environment

```bash
export FORTIOS_HOST="https://192.168.1.99"
export FORTIOS_API_TOKEN="your-api-token"
# Optional:
export FORTIOS_DRY_RUN="true"       # Preview changes without applying
export FORTIOS_VERIFY_SSL="false"   # For self-signed certificates
export FORTIOS_VERSION="7.2"        # Force specific schema version
```

### Multi-Version Support

The server automatically detects your FortiOS version and selects the appropriate schemas. If detection fails, it falls back to the newest available local schemas. You can also force a version:

```bash
# Use schemas for FortiOS 7.2
export FORTIOS_VERSION="7.2"

# Use schemas for FortiOS 7.0
export FORTIOS_VERSION="7.0"
```

**Adding schemas for other versions:**
1. Create folder: `schemas/7.2/`
2. Copy FortiOS 7.2 Swagger JSON files into it
3. Restart server — it will auto-detect and use them

### 3. Run

```bash
npm start
```

## Claude Desktop Configuration

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "fortigate": {
      "command": "node",
      "args": ["/path/to/mcp-fortigate/dist/index.js"],
      "env": {
        "FORTIOS_HOST": "https://192.168.1.99",
        "FORTIOS_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

## Usage Examples

Once connected, ask Claude:

- "Show me all firewall policies"
- "Create a policy to block IP 10.0.0.5"
- "Delete firewall policy ID 42"
- "List all interfaces"
- "Show system status"

## Architecture

```
AI Assistant → MCP Server → FortiOS HTTP Client → FortiGate Device
                    ↓
              Swagger Schemas (72 files)
```

## Development

```bash
# Dev mode with auto-reload
npm run dev

# Run tests
npm test

# Build
npm run build
```

## Environment Variables

### Core
| Variable | Required | Description |
|----------|----------|-------------|
| `FORTIOS_HOST` | Yes | FortiGate URL (https://...) |
| `FORTIOS_API_TOKEN` | Yes | API token for authentication |
| `FORTIOS_DRY_RUN` | No | Preview mode (default: false) |
| `FORTIOS_VERIFY_SSL` | No | SSL verification (default: true) |
| `FORTIOS_VERSION` | No | Force schema version (e.g., 7.2, 7.4, 7.6) |

### Governance (Critical Environments)
| Variable | Required | Description |
|----------|----------|-------------|
| `FORTIOS_READONLY` | No | Default: `true`. Set `false` to allow mutations without change token |
| `FORTIOS_CHANGE_TOKEN` | No | Required for mutations when readonly=true |
| `FORTIOS_OPERATOR_TOKEN` | No | Two-person rule: who proposes changes |
| `FORTIOS_APPROVER_TOKEN` | No | Two-person rule: who approves changes |
| `FORTIOS_EMERGENCY_TOKEN` | No | Required to unfreeze the system |
| `FORTIOS_CHANGE_WINDOW` | No | Maintenance windows: `"Sat 02:00-06:00,Sun 02:00-06:00"` |

### Governance Examples

**Readonly mode (default):**
```bash
export FORTIOS_READONLY="true"
export FORTIOS_CHANGE_TOKEN="chang3-s3cr3t"
# Mutations now require change_token in tool arguments
```

**Two-person rule:**
```bash
export FORTIOS_OPERATOR_TOKEN="op3r4t0r"
export FORTIOS_APPROVER_TOKEN="4ppr0v3r"
# Mutations require both operator AND approver tokens
```

**Emergency freeze:**
```bash
export FORTIOS_EMERGENCY_TOKEN="fr33z3-m3"
# Use fortios_freeze to lock, fortios_unfreeze to unlock
```

**Change windows:**
```bash
export FORTIOS_CHANGE_WINDOW="Sat 02:00-06:00,Sun 02:00-06:00"
# Mutations only allowed during these windows
```

## FortiOS API Token

Generate an API token in FortiOS:

```bash
config system api-user
    edit "mcp-user"
        set api-key generate
        set accprofile "super_admin"
    next
end
```

## License

MIT
