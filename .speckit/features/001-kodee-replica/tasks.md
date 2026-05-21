# Feature 001: Kodee Replica - Implementation Tasks (Kimi Adapted)

> **For Kimi Code CLI workers:** Use `subagent-driven-development` (Agent tool with `subagent_type="coder"`) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking via `SetTodoList`.

**Goal:** Build a production-ready replica of Hostinger's Kodee AI administrative agent with FastAPI, MCP, RAG, and multi-agent orchestration.

**Architecture:** Five-layer async architecture (Presentation → API → Orchestration → MCP → Data) using Python + FastAPI + LangChain + MCP SDK + PostgreSQL + Redis + Qdrant.

**Tech Stack:** Python 3.11, FastAPI, LangChain, OpenAI GPT-4o, FastMCP, Qdrant, PostgreSQL, Redis, Docker Compose

---

## How to Use These Tasks in Kimi

### Task Tracking
Use `SetTodoList` to track progress across all tasks. Update after each task completion.

### Subagent Development
For complex tasks, use the `Agent` tool:
```
subagent_type: "coder"
description: "Implement Task X.Y"
prompt: "You are implementing Task X.Y from the Kodee Replica plan. Read .speckit/features/001-kodee-replica/tasks.md for full context. Follow the steps exactly. Use Shell tool for commands, ReadFile/WriteFile for code."
```

### Tool Mapping (Claude Code → Kimi)
| Claude Code | Kimi |
|-------------|------|
| `TodoWrite` | `SetTodoList` |
| `Bash` | `Shell` |
| `Read` | `ReadFile`, `Grep`, `Glob` |
| `Write` | `WriteFile`, `StrReplaceFile` |
| `Subagent` | `Agent` tool with `subagent_type` |

---

## Phase 1: Foundation

### Task 1.1: Initialize Project Structure

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/main.py` (stub)
- Create: `app/config.py`
- Create: `tests/__init__.py`

**Steps:**

- [ ] **Step 1: Create pyproject.toml with project metadata**
  Use `WriteFile` to create `pyproject.toml` with FastAPI, LangChain, Qdrant, PostgreSQL dependencies.

- [ ] **Step 2: Create requirements.txt**
  Use `Shell` to generate: `pip install poetry 2>/dev/null || true && poetry export -f requirements.txt --without-hashes -o requirements.txt 2>/dev/null || echo "# Manual requirements" > requirements.txt`

- [ ] **Step 3: Create .env.example**
  Use `WriteFile` with all required env vars (OPENAI_API_KEY, DATABASE_URL, REDIS_URL, QDRANT_URL).

- [ ] **Step 4: Create app/config.py with Pydantic Settings**
  Use `WriteFile` for Settings class with `pydantic-settings`.

- [ ] **Step 5: Create app/main.py stub**
  Use `WriteFile` for FastAPI app with `/health` endpoint.

- [ ] **Step 6: Verify project structure**
  Use `Shell`: `ls -la app/ tests/`

- [ ] **Step 7: Commit**
  Use `Shell`: `git add . && git commit -m "feat: initialize project structure"`

**Verification:**
```bash
python -c "from app.main import app; print('OK')"
```

---

### Task 1.2: Docker Compose Setup

**Files:**
- Create: `docker/Dockerfile`
- Create: `docker-compose.yml`
- Create: `alembic.ini`

**Steps:**

- [ ] **Step 1: Create docker/Dockerfile**
  Use `WriteFile` for multi-stage Dockerfile with Python 3.11 slim.

- [ ] **Step 2: Create docker-compose.yml**
  Use `WriteFile` for services: app, db (postgres:15-alpine), redis (redis:7-alpine), qdrant (qdrant/qdrant:latest).

- [ ] **Step 3: Initialize Alembic**
  Use `Shell`: `alembic init alembic 2>/dev/null || echo "alembic not installed yet"`

- [ ] **Step 4: Test Docker Compose**
  Use `Shell`: `docker-compose up -d db redis qdrant`

- [ ] **Step 5: Verify services**
  Use `Shell`: `docker-compose ps`

- [ ] **Step 6: Commit**
  Use `Shell`: `git add . && git commit -m "feat: add docker compose and alembic"`

**Verification:**
```bash
docker-compose ps | grep -E "db|redis|qdrant"
```

---

## Phase 2: API Layer

### Task 2.1: Chat Models and Endpoints

**Files:**
- Create: `app/models/chat.py`
- Create: `app/models/database.py`
- Create: `app/services/chat_service.py`
- Modify: `app/main.py`

**Steps:**

- [ ] **Step 1: Create Pydantic chat models**
  Use `WriteFile` for ChatRequest, ChatResponse with user_id, message, session_id.

- [ ] **Step 2: Create SQLAlchemy models**
  Use `WriteFile` for Conversation, Message tables with UUID, timestamps, JSON fields.

- [ ] **Step 3: Create ChatService**
  Use `WriteFile` for async process_message() stub returning echo response.

- [ ] **Step 4: Wire up endpoints in main.py**
  Use `StrReplaceFile` or `WriteFile` to add POST /chat and WS /ws/{user_id}.

- [ ] **Step 5: Test REST endpoint**
  Use `Shell`: `curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"user_id":"test","message":"hello"}'`

- [ ] **Step 6: Write failing test**
  Use `WriteFile` for `tests/test_chat.py` with pytest-asyncio.

- [ ] **Step 7: Commit**
  Use `Shell`: `git add . && git commit -m "feat: add chat endpoints and models"`

**Verification:**
```bash
pytest tests/test_chat.py -v
```

---

## Phase 3: LLM Integration

### Task 3.1: LLM Service with Tool Calling

**Files:**
- Create: `app/services/llm_service.py`
- Create: `app/agents/base_agent.py`
- Create: `tests/test_llm.py`

**Steps:**

- [ ] **Step 1: Create LLMService**
  Use `WriteFile` with ChatOpenAI, create_tool_calling_agent, AgentExecutor.
  Temperature: 0.2, max_iterations: 5.

- [ ] **Step 2: Create BaseAgent**
  Use `WriteFile` with abstract handle() method.

- [ ] **Step 3: Write failing test for LLM service**
  Use `WriteFile` for test that calls process_with_tools() and asserts response structure.

- [ ] **Step 4: Run test — expect RED**
  Use `Shell`: `pytest tests/test_llm.py -v`

- [ ] **Step 5: Commit**
  Use `Shell`: `git add . && git commit -m "feat: add LLM service with tool calling stub"`

**Verification:**
```bash
pytest tests/test_llm.py -v
```

---

## Phase 4: MCP Server

### Task 4.1: MCP Server with Core Tools

**Files:**
- Create: `app/mcp/server.py`
- Create: `app/mcp/tools/dns_tools.py`
- Create: `app/mcp/tools/backup_tools.py`
- Create: `app/mcp/tools/monitoring_tools.py`

**Steps:**

- [ ] **Step 1: Create MCP Server**
  Use `WriteFile` with `from mcp.server.fastmcp import FastMCP; mcp = FastMCP("kodee-replica")`.

- [ ] **Step 2: Create DNS tools**
  Use `WriteFile` for create_dns_record, list_dns_records with @mcp.tool() decorator.

- [ ] **Step 3: Create Backup tools**
  Use `WriteFile` for create_backup, restore_backup with @mcp.tool() decorator.

- [ ] **Step 4: Create Monitoring tools**
  Use `WriteFile` for check_server_health, get_website_status with @mcp.tool() decorator.

- [ ] **Step 5: Test MCP server starts**
  Use `Shell`: `timeout 5 python app/mcp/server.py 2>&1 || true`

- [ ] **Step 6: Commit**
  Use `Shell`: `git add . && git commit -m "feat: add MCP server with DNS, backup, monitoring tools"`

**Verification:**
```bash
python -c "from app.mcp.server import mcp; print('MCP server loaded:', mcp.name)"
```

---

## Phase 5: MCP Client + Full Agent Flow

### Task 5.1: MCP Client Integration

**Files:**
- Create: `app/mcp/client.py`
- Create: `app/agents/router.py`
- Create: `app/agents/handoff.py`
- Modify: `app/services/chat_service.py`

**Steps:**

- [ ] **Step 1: Create MCPClientService**
  Use `WriteFile` with MultiServerMCPClient, connect_to_server via stdio.

- [ ] **Step 2: Create Agent Router**
  Use `WriteFile` for intent classification using LLM, returns agent type string.

- [ ] **Step 3: Create Handoff Classifier**
  Use `WriteFile` for is_seeking_human() using LLM sentiment analysis.

- [ ] **Step 4: Wire up full chat flow**
  Use `StrReplaceFile` in chat_service.py: handoff check → route → LLM + tools → respond.

- [ ] **Step 5: Test full flow**
  Use `Shell`: `curl -X POST http://localhost:8000/chat -d '{"user_id":"test","message":"check health of server-123"}'`

- [ ] **Step 6: Commit**
  Use `Shell`: `git add . && git commit -m "feat: integrate MCP client, router, and handoff classifier"`

**Verification:**
```bash
pytest tests/test_chat.py tests/test_llm.py -v
```

---

## Phase 6: RAG Pipeline

### Task 6.1: RAG Implementation

**Files:**
- Create: `app/rag/embeddings.py`
- Create: `app/rag/vector_store.py`
- Create: `app/rag/retriever.py`
- Create: `docs/knowledge_base/` (sample docs)

**Steps:**

- [ ] **Step 1: Create RAGService**
  Use `WriteFile` with OpenAIEmbeddings (text-embedding-3-large), QdrantClient.

- [ ] **Step 2: Implement document ingestion**
  Use `WriteFile` for add_documents() with RecursiveCharacterTextSplitter (1000 tokens, 200 overlap).

- [ ] **Step 3: Implement retrieval**
  Use `WriteFile` for retrieve() with cosine similarity, top_k=5.

- [ ] **Step 4: Integrate RAG into chat flow**
  Use `StrReplaceFile` in chat_service.py: retrieve docs → build context → pass to LLM.

- [ ] **Step 5: Add sample knowledge base documents**
  Use `WriteFile` for docs/knowledge_base/getting-started.md.

- [ ] **Step 6: Write RAG test**
  Use `WriteFile` for tests/test_rag.py with ingestion + retrieval test.

- [ ] **Step 7: Commit**
  Use `Shell`: `git add . && git commit -m "feat: add RAG pipeline with Qdrant"`

**Verification:**
```bash
pytest tests/test_rag.py -v
```

---

## Phase 7: Multi-Agent + Polish

### Task 7.1: Specialized Agents

**Files:**
- Create: `app/agents/dns_agent.py`
- Create: `app/agents/backup_agent.py`
- Create: `app/agents/monitoring_agent.py`
- Create: `tests/test_agents.py`

**Steps:**

- [ ] **Step 1: Create DNSAgent**
  Use `WriteFile` extending BaseAgent with DNS-specific system prompt.

- [ ] **Step 2: Create BackupAgent**
  Use `WriteFile` extending BaseAgent with Backup-specific system prompt.

- [ ] **Step 3: Create MonitoringAgent**
  Use `WriteFile` extending BaseAgent with Monitoring-specific system prompt.

- [ ] **Step 4: Update router to dispatch**
  Use `StrReplaceFile` in router.py: AGENTS dict mapping intent → agent instance.

- [ ] **Step 5: Write agent tests**
  Use `WriteFile` for tests/test_agents.py with mocked LLM responses.

- [ ] **Step 6: Run full test suite**
  Use `Shell`: `pytest tests/ --cov=app --cov-report=term-missing`

- [ ] **Step 7: Verify coverage ≥ 80%**
  Use `Shell`: `coverage report | tail -5`

- [ ] **Step 8: Commit**
  Use `Shell`: `git add . && git commit -m "feat: add specialized agents and comprehensive tests"`

**Verification:**
```bash
pytest tests/ -v --tb=short
```

---

## Phase 8: Monitoring & Documentation

### Task 8.1: Monitoring Setup

**Files:**
- Create: `app/utils/monitoring.py`
- Modify: `docker-compose.yml` (add grafana)
- Create: `README.md`

**Steps:**

- [ ] **Step 1: Add Sentry integration**
  Use `WriteFile` for monitoring.py with sentry_sdk.init() if DSN present.

- [ ] **Step 2: Add OpenTelemetry tracing**
  Use `WriteFile` for trace setup with TracerProvider and OTLP exporter.

- [ ] **Step 3: Add Grafana to docker-compose**
  Use `StrReplaceFile` in docker-compose.yml: add grafana service on port 3000.

- [ ] **Step 4: Write README**
  Use `WriteFile` with setup instructions, API endpoints, architecture diagram reference.

- [ ] **Step 5: Final verification**
  Use `Shell`: `docker-compose up --build -d && sleep 5 && curl http://localhost:8000/health`

- [ ] **Step 6: Final test run**
  Use `Shell`: `pytest tests/ -v`

- [ ] **Step 7: Final commit**
  Use `Shell`: `git add . && git commit -m "feat: add monitoring, docs, and finalize MVP"`

**Verification:**
```bash
curl http://localhost:8000/health && echo "OK" || echo "FAIL"
pytest tests/ -q
```

---

## Master Verification Checklist

Use `SetTodoList` to track these before claiming complete:

- [ ] All Docker services start without errors (`docker-compose ps`)
- [ ] `POST /chat` returns valid JSON response
- [ ] WebSocket `/ws/{user_id}` accepts and responds to messages
- [ ] MCP tools are discoverable (`kimi mcp test github` or manual verification)
- [ ] RAG retrieves relevant documents for test queries
- [ ] Test coverage ≥ 80% (`pytest --cov=app`)
- [ ] No hardcoded secrets (`grep -r "sk-" app/ || echo "Clean"`)
- [ ] README has setup instructions
- [ ] `.env.example` has all required variables
- [ ] All commits are atomic with descriptive messages (`git log --oneline`)

---

## Execution Commands for Kimi

### Start implementation
```
SetTodoList with all Phase 1 tasks
ReadFile on tasks.md
Execute Task 1.1 Step 1 using WriteFile
...
```

### Use subagent for parallel tasks
```
Agent subagent_type="coder" description="Implement Phase 1 Foundation"
prompt: "Read .speckit/features/001-kodee-replica/tasks.md and implement all Phase 1 tasks. Use Shell, WriteFile, ReadFile. Commit after each task."
```

### Track progress
```
SetTodoList with updated statuses
```
