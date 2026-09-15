#!/usr/bin/env python3
# Smoke tests for Contract Decision Engine
# Run after: docker compose up -d

import sys
import time
import requests
import json

BASE_URL = "http://localhost"
APP_URL = "http://localhost:8000"

COLORS = {
    'GREEN': '\033[0;32m',
    'RED': '\033[0;31m',
    'YELLOW': '\033[1;33m',
    'NC': '\033[0m'
}

def log_info(msg):
    print(f"{COLORS['YELLOW']}[INFO]{COLORS['NC']} {msg}")

def log_pass(msg):
    print(f"{COLORS['GREEN']}[PASS]{COLORS['NC']} {msg}")

def log_fail(msg):
    print(f"{COLORS['RED']}[FAIL]{COLORS['NC']} {msg}")

def wait_for_service(url, name, max_attempts=30):
    log_info(f"Waiting for {name} at {url}...")
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                log_pass(f"{name} is ready")
                return True
        except Exception:
            pass
        time.sleep(2)
    log_fail(f"{name} not ready after {max_attempts} attempts")
    return False

def test_endpoint(url, expected_status, name):
    try:
        resp = requests.get(url, timeout=10)
        status = resp.status_code
    except Exception as e:
        status = 0

    if status == expected_status:
        log_pass(f"{name}: HTTP {status}")
        return True
    else:
        log_fail(f"{name}: expected {expected_status}, got {status}")
        return False

def test_json_endpoint(url, name, expected_decision):
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        decision = data.get('decision')

        if decision == expected_decision:
            log_pass(f"{name}: decision={decision}")
            return True
        else:
            log_fail(f"{name}: expected decision={expected_decision}, got {decision}")
            return False
    except Exception as e:
        log_fail(f"{name}: request failed - {e}")
        return False

def test_json_array(url, name, field):
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        value = data.get(field)

        if isinstance(value, list):
            log_pass(f"{name}: {field} is array")
            return True
        else:
            log_fail(f"{name}: {field} is not array (type: {type(value).__name__})")
            return False
    except Exception as e:
        log_fail(f"{name}: request failed - {e}")
        return False

def main():
    print("========================================")
    print("  Contract Decision Engine - Smoke Tests")
    print("========================================")
    print("")

    failed = 0

    # 1. Wait for nginx (which proxies to app)
    if not wait_for_service(f"{BASE_URL}/health", "nginx health"):
        failed += 1

    print("")
    log_info("Running endpoint tests...")
    print("")

    # 2. Health endpoints (through nginx)
    if not test_endpoint(f"{BASE_URL}/health", 200, "nginx /health"):
        failed += 1
    if not test_endpoint(f"{BASE_URL}/api/health", 200, "app /api/health via nginx"):
        failed += 1

    # 3. Main page
    if not test_endpoint(f"{BASE_URL}/", 200, "Main page"):
        failed += 1

    # 4. Static files
    if not test_endpoint(f"{BASE_URL}/static/styles.css", 200, "Static CSS"):
        failed += 1
    if not test_endpoint(f"{BASE_URL}/static/js/app.js", 200, "Static JS"):
        failed += 1

    # 5. Demo endpoints
    if not test_json_endpoint(f"{BASE_URL}/analyze/safe", "Demo safe", "safe_to_sign"):
        failed += 1
    if not test_json_endpoint(f"{BASE_URL}/analyze/changes", "Demo changes", "sign_after_changes"):
        failed += 1
    if not test_json_endpoint(f"{BASE_URL}/analyze/reject", "Demo reject", "do_not_sign"):
        failed += 1

    # 6. API analyze endpoint (should return 405 for GET)
    if not test_endpoint(f"{BASE_URL}/api/analyze", 405, "API analyze GET (Method Not Allowed)"):
        failed += 1

    # 7. Tasks list
    if not test_json_array(f"{BASE_URL}/api/tasks/", "Tasks list", "tasks"):
        failed += 1

    print("")
    print("========================================")
    if failed == 0:
        log_pass("ALL SMOKE TESTS PASSED")
        sys.exit(0)
    else:
        log_fail(f"{failed} TEST(S) FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
