# Kodee Replica - Project Constitution

## Vision

Build a production-ready AI administrative agent that replicates the core architecture of Hostinger's Kodee — an LLM-powered system capable of executing real actions via MCP, not just providing text responses.

## Core Principles

### 1. Agent-First Architecture
The system is an **agent**, not a chatbot. It must execute real administrative actions (DNS, backups, monitoring, etc.) through standardized tool interfaces. Text responses are a side effect, not the primary output.

### 2. MCP as the Universal Interface
All tools and actions MUST be exposed through the Model Context Protocol (MCP). No custom tool integrations. The LLM discovers and invokes tools via MCP's standardized primitives (tools, resources, prompts).

### 3. RAG for Factual Grounding
Every response that involves domain knowledge MUST be grounded in retrieved context from the vector database. No hallucinated facts. The RAG pipeline is not optional — it's a core reliability mechanism.

### 4. Multi-Agent Orchestration
The system MUST route requests to specialized agents based on intent. A single monolithic agent does not scale. The router pattern (Supervisor Pattern) is mandatory.

### 5. Human Handoff is a Feature
The system MUST detect when a user needs human assistance and escalate gracefully. A frustrated user forced to interact with an agent is a failed interaction. The Handoff Classifier is critical.

## Technical Standards

### Language & Framework
- **Python 3.11+** as the primary language
- **FastAPI** for the API layer — async by default
- **LangChain / LangGraph** for LLM orchestration
- **MCP SDK (FastMCP)** for tool servers

### Code Quality
- **TDD (Red-Green-Refactor)** for all behavior changes
- **80%+ test coverage** target
- **Type hints everywhere** — no untyped public interfaces
- **DRY and YAGNI** — resist over-engineering

### API Design
- REST + WebSocket for real-time chat
- Pydantic models for all request/response validation
- OpenAPI/Swagger documentation generated automatically
- Rate limiting and auth on all endpoints

### Database & Storage
- **PostgreSQL** for persistent data (conversations, metadata)
- **Redis** for session cache and short-term history
- **Qdrant** for vector storage and semantic search
- **Alembic** for schema migrations

### Infrastructure
- **Docker** for containerization
- **Docker Compose** for local development
- **Kubernetes** manifests for production (future)
- **Grafana + Sentry** for monitoring and error tracking

## Security Posture

### Defense in Depth
1. **Model Layer**: Use models with safety training, implement prompt filters
2. **Application Layer**: Sanitize all inputs, sandbox tool execution, require confirmation for destructive actions
3. **Context Layer**: Access control at retrieval time, data provenance tracking
4. **Monitoring Layer**: Log all prompts, tool calls, and decision paths

### Specific Rules
- NO production code without a failing test first
- NO destructive action without explicit user confirmation
- NO hardcoded secrets — env vars only
- NO direct LLM code execution — tool calls only
- Rate limiting on all external-facing endpoints

## Development Workflow

### SDD / Speckit Methodology
1. **Constitution** ← We are here
2. **Specify** — Define WHAT and WHY for each feature
3. **Plan** — Define tech stack and architecture
4. **Tasks** — Break into actionable, verifiable steps
5. **Implement** — Execute with TDD and subagent review

### Git Workflow
- Feature branches from `main`
- Atomic commits with descriptive messages
- No direct commits to `main`
- PR review before merge (even if self-reviewed)

## Success Criteria

| Metric | Target |
|--------|--------|
| Response time | < 10 seconds for simple queries |
| Tool execution | < 20 seconds end-to-end |
| Test coverage | ≥ 80% |
| RAG context retrieval | < 50ms (p99) |
| Concurrent users | ≥ 100 (MVP) |

## Scope Boundaries

### In Scope (MVP)
- FastAPI backend with REST + WebSocket
- LLM integration (GPT-4o / Claude)
- MCP server with 10-20 core tools
- RAG pipeline with Qdrant
- Multi-agent router + handoff classifier
- PostgreSQL + Redis persistence
- Docker Compose local setup

### Out of Scope (Post-MVP)
- WhatsApp/mobile app frontends
- Kubernetes production deployment
- 500+ tools (start with 10-20)
- Advanced analytics dashboard
- Billing/payment integration
