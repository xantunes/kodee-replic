# Kodee Replica

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI Agent with MCP — a replica of the Hostinger Kodee assistant architecture. This project demonstrates a production-ready multi-agent chat system with RAG, MCP tool integration, real-time WebSocket communication, and structured observability.

## Architecture Overview

The system is organized into **5 layers**:

```
┌─────────────────────────────────────────┐
│  Presentation  (WebSocket / HTTP API)   │
├─────────────────────────────────────────┤
│  API           (FastAPI routes)         │
├─────────────────────────────────────────┤
│  Orchestration (Router + Agents)        │
├─────────────────────────────────────────┤
│  MCP           (Tools & Clients)        │
├─────────────────────────────────────────┤
│  Data          (Postgres + Redis +      │
│                Qdrant vector store)     │
└─────────────────────────────────────────┘
```

1. **Presentation** — Users interact via HTTP (`/chat`) or WebSocket (`/ws/{user_id}`).
2. **API** — FastAPI handles routing, validation, CORS, and monitoring middleware.
3. **Orchestration** — `AgentRouter` classifies intent and delegates to specialized agents (`GeneralAgent`, `DNSAgent`, `BackupAgent`, `MonitoringAgent`).
4. **MCP** — Model Context Protocol server exposes tools (`read_file`, `write_file`, `calculate`, `search_web`, `get_weather`, etc.) consumed by agents.
5. **Data** — PostgreSQL for relational data, Redis for caching/sessions, Qdrant for vector search and RAG document retrieval.

## Features

- **Multi-Agent Routing** — Intent-based classification routes queries to the most appropriate specialized agent (DNS, Backup, Monitoring, General).
- **RAG Pipeline** — Document ingestion, OpenAI embeddings, and Qdrant vector search for context-augmented responses.
- **MCP Tool Integration** — Extensible tool registry with local and remote tool execution via ReAct loop (max 5 iterations).
- **Destructive Action Confirmation** — User confirmation required before executing destructive operations (e.g., `delete_record`, `restore_backup`).
- **Input Sanitization** — Security validation for SQL injection and XSS patterns on all chat inputs.
- **Rate Limiting** — Sliding-window rate limiter middleware with configurable RPS.
- **WebSocket Real-Time Chat** — Stateful bi-directional communication with session tracking.
- **Structured Observability** — JSON logging, Sentry error tracking, OpenTelemetry tracing, Grafana dashboard, and a `/metrics` endpoint.
- **Docker-First Deployment** — Complete `docker-compose.yml` with Postgres, Redis, Qdrant, Jaeger, and Grafana.
- **Async-First** — Built on Python `async`/`await` and FastAPI for high concurrency.
- **Azure OpenAI Support** — Auto-detects Azure OpenAI via `AZURE_OPENAI_ENDPOINT` env var.
- **Per-Agent Model Routing** — Different models for router (mini) vs. domain agents (full).

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API key **or** Azure OpenAI credentials

### 1. Clone and configure

```bash
git clone <repository-url>
cd kodee-replica
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

### 3. Run tests

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the full test suite
pytest -q
```

## API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check — returns status, environment, and version. |
| `POST` | `/chat` | Process a chat message and return an assistant response. |
| `WS` | `/ws/{user_id}` | WebSocket endpoint for real-time chat. |
| `GET` | `/metrics` | Application metrics: uptime, total requests, active sessions. |

### Example: `POST /chat`

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "message": "Hello, Kodee!",
    "session_id": "sess-abc"
  }'
```

**Response:**

```json
{
  "message": "Hello! How can I help you today?",
  "actions": [],
  "session_id": "sess-abc"
}
```

### Example: `GET /metrics`

```bash
curl http://localhost:8000/metrics
```

**Response:**

```json
{
  "uptime_seconds": 42.5,
  "total_requests": 15,
  "active_sessions": 2
}
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅* | — | OpenAI API key for LLM and embeddings. |
| `OPENAI_MODEL` | ❌ | `gpt-4o` | OpenAI model name. |
| `OPENAI_TEMPERATURE` | ❌ | `0.2` | Sampling temperature. |
| `AZURE_OPENAI_ENDPOINT` | ✅* | — | Azure OpenAI endpoint URL. |
| `AZURE_OPENAI_API_KEY` | ✅* | — | Azure OpenAI API key. |
| `AZURE_OPENAI_API_VERSION` | ❌ | `2024-12-01-preview` | Azure API version. |
| `AZURE_OPENAI_DEPLOYMENT` | ❌ | — | Azure deployment name (e.g. `gpt-4.1`). |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | ❌ | `text-embedding-3-small` | Azure embedding deployment. |

\* Provide either `OPENAI_API_KEY` (OpenAI direct) or `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY` (Azure). Azure takes precedence if `AZURE_OPENAI_ENDPOINT` is set.
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string. |
| `REDIS_URL` | ✅ | — | Redis connection string. |
| `QDRANT_URL` | ✅ | — | Qdrant server URL. |
| `QDRANT_COLLECTION` | ❌ | `kodee_knowledge` | Qdrant collection name. |
| `SENTRY_DSN` | ❌ | — | Sentry DSN for error tracking. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | ❌ | `http://jaeger:4317` | OpenTelemetry OTLP endpoint for tracing. |
| `APP_ENV` | ❌ | `development` | Runtime environment. |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). |
| `RATE_LIMIT_RPS` | ❌ | `10` | Rate limit in requests per second. |

### Model Assignment by Agent

You can override which model each agent uses via environment variables:

| Variable | Default | Recommended For |
|----------|---------|----------------|
| `MODEL_ROUTER` | `gpt-4.1-mini` | Fast intent classification |
| `MODEL_GENERAL` | `gpt-4.1-mini` | Chitchat, simple questions |
| `MODEL_DNS` | `gpt-4.1` | DNS management tasks |
| `MODEL_BACKUP` | `gpt-4.1` | Backup and restore operations |
| `MODEL_MONITORING` | `gpt-4.1` | Infrastructure monitoring |
| `MODEL_HANDOFF` | `gpt-4.1-mini` | Human escalation detection |

**Strategy:** Use `gpt-4.1-mini` for ~70% of traffic (router, general, handoff) and `gpt-4.1` for the ~30% that needs deep reasoning (DNS, backup, monitoring).

## Project Structure

```
.
├── app/
│   ├── __init__.py              # Package version info
│   ├── main.py                  # FastAPI application, lifespan, routes
│   ├── config.py                # Pydantic Settings
│   ├── utils/
│   │   ├── monitoring.py        # Logging, Sentry, OpenTelemetry, request middleware
│   │   ├── security.py          # Input validation and sanitization
│   │   ├── rate_limit.py        # Rate limiting middleware
│   │   └── session_store.py     # In-memory and Redis session storage
│   ├── agents/
│   │   ├── base_agent.py        # BaseAgent abstract class
│   │   ├── domain_agent.py      # SDD-compliant agent exports
│   │   ├── router.py            # Intent-based AgentRouter
│   │   ├── orchestrator.py      # Multi-turn conversation orchestrator
│   │   └── specialized.py       # Concrete agent implementations (DNS, Backup, Monitoring, General)
│   ├── llm/
│   │   ├── model_resolver.py    # Per-agent model routing
│   │   └── tool_registry.py     # Local tool registry
│   │   ├── prompts.py           # System prompts & message builders
│   │   └── tool_registry.py     # Local tool registry
│   ├── mcp/
│   │   ├── client.py            # MCP client for remote tools
│   │   └── server.py            # MCP server with built-in tools
│   ├── models/
│   │   ├── chat.py              # Pydantic request/response models
│   │   └── database.py          # SQLAlchemy models
│   ├── rag/
│   │   ├── embeddings.py        # OpenAI embedding service
│   │   ├── vector_store.py      # Qdrant vector store client
│   │   ├── ingest.py            # Document chunking & ingestion
│   │   └── retriever.py         # RAG retrieval & prompt augmentation
│   └── services/
│       ├── chat_service.py      # Business logic & orchestrator wiring
│       └── llm_service.py       # LLM wrapper (LangChain + OpenAI / Azure)
├── tests/
│   ├── conftest.py              # Shared pytest fixtures
│   ├── test_agents.py           # Agent routing & orchestration tests
│   ├── test_chat.py             # HTTP chat endpoint tests
│   ├── test_websocket.py        # WebSocket endpoint tests
│   ├── test_llm.py              # LLM service & tool registry tests
│   ├── test_mcp.py              # MCP server & client tests
│   ├── test_rag.py              # RAG pipeline tests
│   ├── test_integration.py      # Integration tests
│   └── test_monitoring.py       # Monitoring & metrics tests
├── docker/
│   └── Dockerfile               # Application container image
├── docker-compose.yml           # Full stack orchestration
├── pyproject.toml               # Project metadata & dependencies
├── .env.example                 # Example environment configuration
└── README.md                    # This file
```

## Testing

The project uses **pytest** with async support via `pytest-asyncio`.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run a specific test file
pytest tests/test_monitoring.py -v
```

Key test categories:

- **Unit tests** — Individual components (agents, LLM service, RAG, MCP tools).
- **Integration tests** — End-to-end chat flow via HTTP and WebSocket.
- **Monitoring tests** — Metrics endpoint, health checks, and middleware logging.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
