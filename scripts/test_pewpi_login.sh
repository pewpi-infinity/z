#!/bin/bash
# test_pewpi_login.sh — Integration test for pewpi_login.py
#
# This script:
# 1. Starts the server on an ephemeral port
# 2. Adds a test user
# 3. Tests login with valid and invalid credentials
# 4. Cleans up

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"
TEST_PORT=18080
TEST_USER="testuser"
TEST_PASS="testpass123"
TEST_IP="192.168.100.50"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

cleanup() {
    log_info "Cleaning up..."
    
    # Kill the server if running
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    
    # Remove test credentials
    if [ -f "$SCRIPT_DIR/credentials.json" ]; then
        rm -f "$SCRIPT_DIR/credentials.json"
        log_info "Removed credentials.json"
    fi
    
    # Restore empty credentials file
    echo '{}' > "$SCRIPT_DIR/credentials.json"
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Check if curl is available
if ! command -v curl &> /dev/null; then
    log_error "curl is required but not installed"
    exit 1
fi

# Check if Python script exists
if [ ! -f "$SCRIPT_DIR/pewpi_login.py" ]; then
    log_error "pewpi_login.py not found in $SCRIPT_DIR"
    exit 1
fi

log_info "Starting pewpi_login integration tests"
log_info "Script directory: $SCRIPT_DIR"
log_info "Test port: $TEST_PORT"

# Step 1: Add a test user
log_info "Adding test user: $TEST_USER"
"$PYTHON" "$SCRIPT_DIR/pewpi_login.py" add-user "$TEST_USER" "$TEST_PASS" --ips "$TEST_IP,127.0.0.1"

if [ ! -f "$SCRIPT_DIR/credentials.json" ]; then
    log_error "credentials.json was not created"
    exit 1
fi

log_info "User added successfully"

# Step 2: Start the server in background
log_info "Starting server on port $TEST_PORT..."
"$PYTHON" "$SCRIPT_DIR/pewpi_login.py" run --host 127.0.0.1 --port "$TEST_PORT" &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Check if server is running
if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    log_error "Server failed to start"
    exit 1
fi

log_info "Server started with PID $SERVER_PID"

# Step 3: Test health endpoint
log_info "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "http://127.0.0.1:$TEST_PORT/health")
if echo "$HEALTH_RESPONSE" | grep -q '"ok": true'; then
    log_info "Health check passed: $HEALTH_RESPONSE"
else
    log_error "Health check failed: $HEALTH_RESPONSE"
    exit 1
fi

# Step 4: Test login with valid credentials and valid IP (via X-Forwarded-For)
log_info "Testing login with valid credentials and valid IP..."
LOGIN_RESPONSE=$(curl -s -X POST "http://127.0.0.1:$TEST_PORT/login" \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: $TEST_IP" \
    -d "{\"username\": \"$TEST_USER\", \"password\": \"$TEST_PASS\"}")

if echo "$LOGIN_RESPONSE" | grep -q '"ok": true'; then
    log_info "Login succeeded (expected): $LOGIN_RESPONSE"
else
    log_error "Login should have succeeded: $LOGIN_RESPONSE"
    exit 1
fi

# Step 5: Test login with valid credentials but invalid IP
log_info "Testing login with valid credentials but invalid IP..."
INVALID_IP_RESPONSE=$(curl -s -X POST "http://127.0.0.1:$TEST_PORT/login" \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: 10.10.10.10" \
    -d "{\"username\": \"$TEST_USER\", \"password\": \"$TEST_PASS\"}")

if echo "$INVALID_IP_RESPONSE" | grep -q '"ok": false'; then
    log_info "Login rejected due to invalid IP (expected): $INVALID_IP_RESPONSE"
else
    log_error "Login should have been rejected: $INVALID_IP_RESPONSE"
    exit 1
fi

# Step 6: Test login with invalid password
log_info "Testing login with invalid password..."
INVALID_PASS_RESPONSE=$(curl -s -X POST "http://127.0.0.1:$TEST_PORT/login" \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: $TEST_IP" \
    -d "{\"username\": \"$TEST_USER\", \"password\": \"wrongpassword\"}")

if echo "$INVALID_PASS_RESPONSE" | grep -q '"ok": false'; then
    log_info "Login rejected due to invalid password (expected): $INVALID_PASS_RESPONSE"
else
    log_error "Login should have been rejected: $INVALID_PASS_RESPONSE"
    exit 1
fi

# Step 7: Test login with invalid username
log_info "Testing login with invalid username..."
INVALID_USER_RESPONSE=$(curl -s -X POST "http://127.0.0.1:$TEST_PORT/login" \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: $TEST_IP" \
    -d "{\"username\": \"nonexistent\", \"password\": \"somepass\"}")

if echo "$INVALID_USER_RESPONSE" | grep -q '"ok": false'; then
    log_info "Login rejected due to invalid username (expected): $INVALID_USER_RESPONSE"
else
    log_error "Login should have been rejected: $INVALID_USER_RESPONSE"
    exit 1
fi

# Step 8: Test with 127.0.0.1 (also in allowed list)
log_info "Testing login with 127.0.0.1 IP..."
LOCAL_IP_RESPONSE=$(curl -s -X POST "http://127.0.0.1:$TEST_PORT/login" \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: 127.0.0.1" \
    -d "{\"username\": \"$TEST_USER\", \"password\": \"$TEST_PASS\"}")

if echo "$LOCAL_IP_RESPONSE" | grep -q '"ok": true'; then
    log_info "Login with 127.0.0.1 succeeded (expected): $LOCAL_IP_RESPONSE"
else
    log_error "Login should have succeeded: $LOCAL_IP_RESPONSE"
    exit 1
fi

echo ""
log_info "========================================="
log_info "All tests passed!"
log_info "========================================="
