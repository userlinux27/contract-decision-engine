#!/bin/bash
# Smoke tests for Contract Decision Engine
# Run after: docker compose up -d

set -e

BASE_URL="http://localhost"
APP_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; }

# Wait for services to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    log_info "Waiting for $name at $url..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            log_pass "$name is ready"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    log_fail "$name not ready after $max_attempts attempts"
    return 1
}

# Test endpoint
test_endpoint() {
    local url=$1
    local expected_status=$2
    local name=$3
    
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$status" = "$expected_status" ]; then
        log_pass "$name: HTTP $status"
        return 0
    else
        log_fail "$name: expected $expected_status, got $status"
        return 1
    fi
}

# Test JSON response
test_json_endpoint() {
    local url=$1
    local name=$2
    local expected_decision=$3
    
    local response=$(curl -s "$url" 2>/dev/null)
    local status=$?
    
    if [ $status -ne 0 ]; then
        log_fail "$name: curl failed"
        return 1
    fi
    
    # Extract decision field using jq
    local decision=$(echo "$response" | jq -r '.decision // empty' 2>/dev/null)
    
    if [ "$decision" = "$expected_decision" ]; then
        log_pass "$name: decision=$decision"
        return 0
    else
        log_fail "$name: expected decision=$expected_decision, got $decision"
        echo "Response: $response"
        return 1
    fi
}

# Test JSON array response
test_json_array() {
    local url=$1
    local name=$2
    local field=$3
    
    local response=$(curl -s "$url" 2>/dev/null)
    local status=$?
    
    if [ $status -ne 0 ]; then
        log_fail "$name: curl failed"
        return 1
    fi
    
    local is_array=$(echo "$response" | jq -e "$field | type == \"array\"" 2>/dev/null && echo true || echo false)
    
    if [ "$is_array" = "true" ]; then
        log_pass "$name: $field is array"
        return 0
    else
        log_fail "$name: $field is not array"
        echo "Response: $response"
        return 1
    fi
}

main() {
    echo "========================================"
    echo "  Contract Decision Engine - Smoke Tests"
    echo "========================================"
    echo ""
    
    local failed=0
    
    # 1. Wait for nginx (which proxies to app)
    wait_for_service "$BASE_URL/health" "nginx health" || failed=1
    
    echo ""
    log_info "Running endpoint tests..."
    echo ""
    
    # 2. Health endpoints (through nginx)
    test_endpoint "$BASE_URL/health" "200" "nginx /health" || failed=1
    test_endpoint "$BASE_URL/api/health" "200" "app /api/health via nginx" || failed=1
    
    # 3. Main page
    test_endpoint "$BASE_URL/" "200" "Main page" || failed=1
    
    # 4. Static files
    test_endpoint "$BASE_URL/static/styles.css" "200" "Static CSS" || failed=1
    test_endpoint "$BASE_URL/static/js/app.js" "200" "Static JS" || failed=1
    
    # 5. Demo endpoints
    test_json_endpoint "$BASE_URL/analyze/safe" "Demo safe" "safe_to_sign" || failed=1
    test_json_endpoint "$BASE_URL/analyze/changes" "Demo changes" "sign_after_changes" || failed=1
    test_json_endpoint "$BASE_URL/analyze/reject" "Demo reject" "do_not_sign" || failed=1
    
    # 6. API analyze endpoint (should return 405 for GET)
    test_endpoint "$BASE_URL/api/analyze" "405" "API analyze GET (Method Not Allowed)" || failed=1
    
    # 7. Tasks list
    test_json_array "$BASE_URL/api/tasks/" "Tasks list" ".tasks" || failed=1
    
    echo ""
    echo "========================================"
    if [ $failed -eq 0 ]; then
        log_pass "ALL SMOKE TESTS PASSED"
        exit 0
    else
        log_fail "$failed TEST(S) FAILED"
        exit 1
    fi
}

main "$@"