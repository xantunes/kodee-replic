# Feature 001: Kodee Replica - Technical Implementation Plan

## Architecture Overview

Five-layer architecture matching the Kodee reference:
1. **Presentation** — Chat interface (hPanel, REST, WebSocket)
2. **API** — FastAPI + Gunicorn, Auth, Rate Limiting
3. **Orchestration** — Handoff Classifier, Agent Router, AI Agent, RAG Engine
4. **MCP (Tools)** — MCP Server, External APIs, Internal APIs, MCP Client
5. **Data** — PostgreSQL, Redis, Vector DB, Monitoring, Kubernetes

## Tech Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| API Framework | FastAPI + Gunicorn | Native async, Pydantic validation, auto OpenAPI docs |
| Language | Python 3.11+ | Mature AI ecosystem, LangChain integration |
| LLM | GPT-4o via OpenAI API | Advanced tool calling, low latency |
| Orchestration | LangChain + LangGraph | Provider-agnostic, complex workflows, MCP integration |
| Protocol | MCP (Model Context Protocol) | Standardized tool discovery, open-source |
| MCP Server | FastMCP (Python SDK) | Official SDK, @tool decorators, FastAPI integration |
| Vector DB | Qdrant | Speed + filtering, open-source, ~$45/mo self-hosted |
| Relational DB | PostgreSQL + Alembic | ACID transactions, migration management |
| Cache | Redis | High-speed in-memory, native TTL |
| Container | Docker + Docker Compose | Consistency across environments |
| Monitoring | Grafana + Sentry | Metrics visualization + error tracking |

## File Structure

```
kodee-replica/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Pydantic Settings
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── router.py           # Agent Router (intent classification)
│   │   ├── base_agent.py       # Base handler for all agents
│   │   ├── domain_agent.py     # Specialized domain agents
│   │   └── handoff.py          # Handoff Classifier
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py           # MCP Server setup (FastMCP)
│   │   ├── client.py           # MCP Client (LangChain integration)
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── dns_tools.py
│   │       ├── backup_tools.py
│   │       ├── monitoring_tools.py
│   │       └── user_tools.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embeddings.py       # OpenAI embeddings config
│   │   ├── vector_store.py     # Qdrant integration
│   │   └── retriever.py        # Retrieval logic
│   ├── models/
│   │   ├── __init__.py
│   │   ├── chat.py             # Pydantic request/response models
│   │   └── database.py         # SQLAlchemy models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_service.py     # Main chat orchestration
│   │   └── llm_service.py      # LLM integration
│   └── utils/
│       ├── monitoring.py       # Grafana/Sentry integration
│       └── security.py         # Input validation, sanitization
├── alembic/                    # Database migrations
├── tests/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/
│   └── knowledge_base/         # Documents for RAG ingestion
├── .env.example
├── requirements.txt
└── pyproject.toml
```

## Implementation Phases

### Phase 1: Foundation (Days 1-2)
**Goal:** Project structure, Docker Compose, basic FastAPI app

- Initialize project with poetry/pip
- Create Docker Compose (app, postgres, redis, qdrant)
- Basic FastAPI app with health endpoint
- Pydantic Settings with `.env` support
- Alembic initialized

### Phase 2: API Layer (Days 3-4)
**Goal:** REST + WebSocket endpoints for chat

- `POST /chat` endpoint with request/response models
- WebSocket `/ws/{user_id}` for real-time chat
- Session management with Redis
- Rate limiting middleware
- Error handling and logging

### Phase 3: LLM Integration (Days 5-6)
**Goal:** LLM service with tool calling capability

- LangChain ChatOpenAI setup
- Tool registration system
- ReAct agent with max_iterations=5
- Chat history management
- System prompt engineering

### Phase 4: MCP Server (Days 7-9)
**Goal:** MCP Server with 10+ tools

- FastMCP server setup
- Tool definitions with schemas:
  - DNS: create_record, list_records, delete_record
  - Backup: create_backup, restore_backup, list_backups
  - Monitoring: check_server_health, get_website_status
  - User: get_user_info, list_user_sites
- Tool execution with real (or mocked) API calls
- Server running on stdio

### Phase 5: MCP Client + Agent (Days 10-12)
**Goal:** Agent discovers and uses MCP tools

- MultiServerMCPClient integration
- Dynamic tool discovery
- Agent Router (intent classification)
- Handoff Classifier
- Full chat flow: receive → route → LLM → tool call → execute → respond

### Phase 6: RAG Pipeline (Days 13-15)
**Goal:** Knowledge base retrieval for grounded responses

- Document ingestion pipeline
- RecursiveCharacterTextSplitter (1000 tokens, 200 overlap)
- OpenAI text-embedding-3-large
- Qdrant collection setup
- Retrieval-augmented generation in chat flow

### Phase 7: Multi-Agent + Polish (Days 16-18)
**Goal:** Specialized agents and production polish

- Domain-specific agents (DNSAgent, BackupAgent, etc.)
- Supervisor pattern for routing
- Handoff to human workflow
- Comprehensive tests (≥80% coverage)
- Security: input sanitization, sandboxing

### Phase 8: Monitoring & Docs (Days 19-20)
**Goal:** Observability and documentation

- OpenTelemetry tracing
- Sentry error tracking
- Grafana dashboard setup
- API documentation (auto-generated)
- README with setup instructions

## Database Schema

```sql
-- conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(50) NOT NULL, -- user, assistant, system, tool
    content TEXT NOT NULL,
    tool_calls JSONB,
    tool_call_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- tool_executions
CREATE TABLE tool_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    tool_name VARCHAR(255) NOT NULL,
    arguments JSONB,
    result JSONB,
    success BOOLEAN NOT NULL,
    duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Environment Variables

```bash
# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.2

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/kodee
REDIS_URL=redis://redis:6379/0

# Vector DB
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=kodee_knowledge

# Monitoring
SENTRY_DSN=https://...
GRAFANA_ADMIN_PASSWORD=admin

# App
APP_ENV=development
LOG_LEVEL=INFO
RATE_LIMIT_RPS=10
```

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenAI API latency | High | Async architecture, timeout handling, fallback messages |
| MCP tool failures | High | Try/catch all tool calls, graceful degradation |
| Token limit overflow | Medium | Context summarization, trim old messages |
| RAG retrieval misses | Medium | Fallback to "I don't know", manual knowledge base curation |
| Prompt injection | High | Input sanitization, sandboxed tool execution, human confirmation for destructive actions |
| Scope creep | Medium | Strict MVP boundary, 20-day timeline, YAGNI enforcement |
