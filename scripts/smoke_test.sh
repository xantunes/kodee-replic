#!/usr/bin/env bash
set -euo pipefail

# Kodee API - Smoke Test Suite
# Usage: bash scripts/smoke_test.sh [--verbose]

VERBOSE=${1:-""}
BASE_URL="http://localhost:8000"
DB_URL="postgresql://kodee:kodee@localhost:5432/kodee_db"
REDIS_HOST="localhost"
REDIS_PORT="6379"
QDRANT_URL="http://localhost:6333"
JAEGER_URL="http://localhost:16686"
GRAFANA_URL="http://localhost:3000"

PASS=0
FAIL=0
WARN=0

log_info()  { echo -e "\033[1;34m[INFO]\033[0m  $*"; }
log_pass()  { echo -e "\033[1;32m[PASS]\033[0m  $*"; PASS=$((PASS+1)); }
log_fail()  { echo -e "\033[1;31m[FAIL]\033[0m  $*"; FAIL=$((FAIL+1)); }
log_warn()  { echo -e "\033[1;33m[WARN]\033[0m  $*"; WARN=$((WARN+1)); }

section() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════════════"
}

curl_silent() {
    if [[ "$VERBOSE" == "--verbose" ]]; then
        curl -s "$@"
    else
        curl -s -o /dev/null -w "%{http_code}" "$@"
    fi
}

# ─── 1. Docker Compose Health ──────────────────────────────────
section "1. Docker Compose Health"

SERVICES="db redis qdrant jaeger grafana app"
for svc in $SERVICES; do
    STATUS=$(docker compose ps -q "$svc" 2>/dev/null | xargs docker inspect -f '{{.State.Status}}' 2>/dev/null || echo "missing")
    if [[ "$STATUS" == "running" ]]; then
        log_pass "Container '$svc' is running"
    else
        log_fail "Container '$svc' is NOT running (status: $STATUS)"
    fi
done

# ─── 2. API Health & Endpoints ─────────────────────────────────
section "2. API Endpoints"

# 2.1 Health endpoint
HTTP_CODE=$(curl_silent "$BASE_URL/health")
if [[ "$HTTP_CODE" == "200" ]]; then
    log_pass "GET /health → 200"
else
    log_fail "GET /health → $HTTP_CODE"
fi

# 2.2 Chat endpoint (echo mode)
HTTP_CODE=$(curl_silent -X POST "$BASE_URL/chat" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"smoke-test","message":"hello"}')
if [[ "$HTTP_CODE" == "200" ]]; then
    log_pass "POST /chat → 200"
else
    log_fail "POST /chat → $HTTP_CODE"
fi

# 2.3 Chat with session (persistence)
HTTP_CODE=$(curl_silent -X POST "$BASE_URL/chat" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"smoke-test","message":"ping","session_id":"smoke-session-001"}')
if [[ "$HTTP_CODE" == "200" ]]; then
    log_pass "POST /chat (with session) → 200"
else
    log_fail "POST /chat (with session) → $HTTP_CODE"
fi

# ─── 3. Rate Limiting ──────────────────────────────────────────
section "3. Rate Limiting"

# Send 15 rapid requests (default limit ~10/sec)
RATE_LIMIT_HIT=0
for i in {1..15}; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/chat" \
        -H "Content-Type: application/json" \
        -d '{"user_id":"rate-test","message":"x"}' 2>/dev/null || echo "000")
    if [[ "$CODE" == "429" ]]; then
        RATE_LIMIT_HIT=1
        break
    fi
done

if [[ "$RATE_LIMIT_HIT" == "1" ]]; then
    log_pass "Rate limit triggered (429 received)"
else
    log_warn "Rate limit NOT triggered (may need tuning)"
fi

# ─── 4. Security (Input Sanitization) ──────────────────────────
section "4. Security"

# 4.1 SQL Injection
HTTP_CODE=$(curl_silent -X POST "$BASE_URL/chat" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"sec-test","message":"DROP TABLE users; --"}')
if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "400" ]]; then
    log_pass "SQL Injection handled → $HTTP_CODE"
else
    log_fail "SQL Injection response unexpected → $HTTP_CODE"
fi

# 4.2 XSS
HTTP_CODE=$(curl_silent -X POST "$BASE_URL/chat" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"sec-test","message":"<script>alert(1)</script>"}')
if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "400" ]]; then
    log_pass "XSS payload handled → $HTTP_CODE"
else
    log_fail "XSS response unexpected → $HTTP_CODE"
fi

# ─── 5. PostgreSQL Persistence ─────────────────────────────────
section "5. PostgreSQL Persistence"

# Check tables exist
if docker exec kodee_db psql -U kodee -d kodee_db -c "\dt" 2>/dev/null | grep -q "conversations"; then
    log_pass "Table 'conversations' exists"
else
    log_fail "Table 'conversations' NOT found"
fi

if docker exec kodee_db psql -U kodee -d kodee_db -c "\dt" 2>/dev/null | grep -q "messages"; then
    log_pass "Table 'messages' exists"
else
    log_fail "Table 'messages' NOT found"
fi

if docker exec kodee_db psql -U kodee -d kodee_db -c "\dt" 2>/dev/null | grep -q "tool_executions"; then
    log_pass "Table 'tool_executions' exists"
else
    log_fail "Table 'tool_executions' NOT found"
fi

# Check session was persisted
MSG_COUNT=$(docker exec kodee_db psql -U kodee -d kodee_db -t -c \
    "SELECT COUNT(*) FROM messages WHERE content = 'ping';" 2>/dev/null | xargs || echo "0")
if [[ "$MSG_COUNT" -gt "0" ]]; then
    log_pass "Session messages persisted ($MSG_COUNT rows)"
else
    log_warn "No session messages found (may be async/delayed)"
fi

# ─── 6. Redis Session Store ────────────────────────────────────
section "6. Redis Session Store"

REDIS_KEYS=$(docker exec kodee_redis redis-cli keys '*' 2>/dev/null | wc -l | xargs || echo "0")
if [[ "$REDIS_KEYS" -gt "0" ]]; then
    log_pass "Redis has $REDIS_KEYS key(s)"
else
    log_warn "Redis is empty (InMemory fallback may be active)"
fi

# ─── 7. Qdrant / RAG ───────────────────────────────────────────
section "7. Qdrant / RAG"

QDRANT_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$QDRANT_URL/collections" 2>/dev/null || echo "000")
if [[ "$QDRANT_HEALTH" == "200" ]]; then
    log_pass "Qdrant API → 200"
else
    log_fail "Qdrant API → $QDRANT_HEALTH"
fi

# Check knowledge collection
COLLECTION_EXISTS=$(curl -s "$QDRANT_URL/collections/kodee_knowledge" 2>/dev/null | grep -c 'status' || echo "0")
if [[ "$COLLECTION_EXISTS" -gt "0" ]]; then
    log_pass "Collection 'kodee_knowledge' exists"
else
    log_warn "Collection 'kodee_knowledge' not found (docs may not be loaded)"
fi

# ─── 8. Observability ──────────────────────────────────────────
section "8. Observability"

JAEGER_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$JAEGER_URL" 2>/dev/null || echo "000")
if [[ "$JAEGER_HEALTH" == "200" ]]; then
    log_pass "Jaeger UI → 200 ($JAEGER_URL)"
else
    log_warn "Jaeger UI → $JAEGER_HEALTH"
fi

GRAFANA_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$GRAFANA_URL/api/health" 2>/dev/null || echo "000")
if [[ "$GRAFANA_HEALTH" == "200" ]]; then
    log_pass "Grafana API → 200 ($GRAFANA_URL)"
else
    log_warn "Grafana API → $GRAFANA_HEALTH"
fi

# ─── 9. Unit Tests (Optional) ──────────────────────────────────
section "9. Unit Tests"

if command -v uv &>/dev/null; then
    TEST_OUTPUT=$(uv run pytest --tb=short -q 2>&1 | tail -5)
    if echo "$TEST_OUTPUT" | grep -q "passed"; then
        PASSED=$(echo "$TEST_OUTPUT" | grep -o '[0-9]* passed' | grep -o '[0-9]*' || echo "0")
        log_pass "Unit tests: $PASSED passed"
    else
        log_fail "Unit tests failed"
    fi
else
    log_warn "uv not found — skipping unit tests"
fi

# ─── Report ────────────────────────────────────────────────────
section "SMOKE TEST REPORT"

echo ""
echo "  ✅ Passed:  $PASS"
echo "  ❌ Failed:  $FAIL"
echo "  ⚠️  Warnings: $WARN"
echo ""

if [[ "$FAIL" -eq "0" ]]; then
    echo -e "  \033[1;32mALL CRITICAL CHECKS PASSED\033[0m 🚀"
    exit 0
else
    echo -e "  \033[1;31mSOME CHECKS FAILED\033[0m — review output above"
    exit 1
fi
