#!/usr/bin/env bash
# deploy/smoke_test.sh — Verify image-to-text.fit is serving
# Usage: bash deploy/smoke_test.sh [domain]
# Example: bash deploy/smoke_test.sh image-to-text.fit
set -euo pipefail

DOMAIN="${1:-image-to-text.fit}"
BASE_URL="https://${DOMAIN}"
PASS=0
FAIL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[PASS]${NC} $1"; PASS=$((PASS+1)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; FAIL=$((FAIL+1)); }
info() { echo -e "${YELLOW}[INFO]${NC} $1"; }

echo ""
echo "=================================================="
echo "  Image to Text — Smoke Test"
echo "  Target: ${BASE_URL}"
echo "=================================================="
echo ""

# Helper: poll a URL until expected code(s) or timeout
poll_url() {
    local url="$1"
    local label="$2"
    local timeout=30
    local code="000"
    for i in $(seq 1 "${timeout}"); do
        code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${url}" 2>/dev/null || echo "000")
        if [ "${code}" != "000" ]; then
            break
        fi
        sleep 1
    done
    echo "${code}"
}

# ---------------------------------------------------------------------------
# Check root path returns 200, 301, or 302
# ---------------------------------------------------------------------------
info "GET ${BASE_URL}/"
ROOT_CODE=$(poll_url "${BASE_URL}/" "GET /")
if [ "${ROOT_CODE}" = "200" ] || [ "${ROOT_CODE}" = "301" ] || [ "${ROOT_CODE}" = "302" ]; then
    ok "GET / returned HTTP ${ROOT_CODE}"
else
    fail "GET / returned HTTP ${ROOT_CODE} (expected 200, 301, or 302)"
fi

# ---------------------------------------------------------------------------
# Check /api/health returns 200 (poll up to 30s for rolling restart)
# ---------------------------------------------------------------------------
info "GET ${BASE_URL}/api/health"
HEALTH_CODE="000"
for i in $(seq 1 30); do
    HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${BASE_URL}/api/health" 2>/dev/null || echo "000")
    if [ "${HEALTH_CODE}" = "200" ]; then
        break
    fi
    sleep 1
done
if [ "${HEALTH_CODE}" = "200" ]; then
    ok "GET /api/health returned HTTP ${HEALTH_CODE}"
else
    fail "GET /api/health returned HTTP ${HEALTH_CODE} (expected 200)"
fi

# ---------------------------------------------------------------------------
# Check /api/health response body contains status field
# ---------------------------------------------------------------------------
info "Checking /api/health JSON body..."
HEALTH_BODY=$(curl -s --max-time 15 "${BASE_URL}/api/health" 2>/dev/null || echo "")
if echo "${HEALTH_BODY}" | grep -q '"status"'; then
    ok "/api/health returns JSON with 'status' field"
else
    fail "/api/health response missing 'status' field. Body: ${HEALTH_BODY:0:200}"
fi

# ---------------------------------------------------------------------------
# Check www redirect to apex
# ---------------------------------------------------------------------------
info "Checking www redirect..."
WWW_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 -L "https://www.${DOMAIN}/" 2>/dev/null || echo "000")
if [ "${WWW_CODE}" = "200" ]; then
    ok "www.${DOMAIN} redirects to apex (final HTTP ${WWW_CODE})"
else
    info "www.${DOMAIN} redirect check returned ${WWW_CODE} (non-fatal if DNS not set)"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "=================================================="
if [ "${FAIL}" -eq 0 ]; then
    echo -e "${GREEN}ALL ${PASS} CHECKS PASSED${NC}"
    echo ""
    echo "  Site is live at: ${BASE_URL}"
else
    echo -e "${RED}${FAIL} CHECK(S) FAILED — ${PASS} passed${NC}"
    echo "  Fix the [FAIL] items above before considering the deploy complete."
    exit 1
fi
echo "=================================================="
echo ""

