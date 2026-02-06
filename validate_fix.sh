#!/bin/bash
# =============================================================================
# Final Validation - Docker PORT Fix
# =============================================================================
# Validates all aspects of the Docker PORT environment variable fix
# =============================================================================

set -e

echo "================================================================================"
echo "DOCKER PORT FIX - FINAL VALIDATION"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

# Test 1: Check files exist
echo "Test 1: Verifying required files exist..."
FILES=(
    "Dockerfile"
    "scripts/docker-entrypoint.sh"
    "test_docker_port.py"
    "test_docker_runtime.py"
    "DOCKER_PORT_FIX_SUMMARY.md"
    "DOCKER_PORT_FIX_COMPARISON.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file exists"
    else
        echo -e "${RED}✗${NC} $file missing"
        ERRORS=$((ERRORS + 1))
    fi
done

# Test 2: Check script is executable
echo ""
echo "Test 2: Verifying script permissions..."
if [ -x "scripts/docker-entrypoint.sh" ]; then
    echo -e "${GREEN}✓${NC} docker-entrypoint.sh is executable"
else
    echo -e "${RED}✗${NC} docker-entrypoint.sh is not executable"
    ERRORS=$((ERRORS + 1))
fi

# Test 3: Check script syntax
echo ""
echo "Test 3: Validating script syntax..."
if bash -n scripts/docker-entrypoint.sh; then
    echo -e "${GREEN}✓${NC} docker-entrypoint.sh syntax is valid"
else
    echo -e "${RED}✗${NC} docker-entrypoint.sh has syntax errors"
    ERRORS=$((ERRORS + 1))
fi

# Test 4: Check Dockerfile references script
echo ""
echo "Test 4: Verifying Dockerfile uses startup script..."
if grep -q "docker-entrypoint.sh" Dockerfile; then
    echo -e "${GREEN}✓${NC} Dockerfile references docker-entrypoint.sh"
else
    echo -e "${RED}✗${NC} Dockerfile does not reference docker-entrypoint.sh"
    ERRORS=$((ERRORS + 1))
fi

# Test 5: Check HEALTHCHECK uses PORT fallback
echo ""
echo "Test 5: Verifying HEALTHCHECK uses PORT fallback..."
if grep -q '\${PORT:-5000}' Dockerfile; then
    echo -e "${GREEN}✓${NC} HEALTHCHECK uses PORT fallback syntax"
else
    echo -e "${RED}✗${NC} HEALTHCHECK missing PORT fallback"
    ERRORS=$((ERRORS + 1))
fi

# Test 6: Run Python tests
echo ""
echo "Test 6: Running Python validation tests..."
if python test_docker_port.py > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} test_docker_port.py passed"
else
    echo -e "${RED}✗${NC} test_docker_port.py failed"
    ERRORS=$((ERRORS + 1))
fi

if python test_port_fix.py > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} test_port_fix.py passed"
else
    echo -e "${RED}✗${NC} test_port_fix.py failed"
    ERRORS=$((ERRORS + 1))
fi

# Test 7: Check Docker image exists
echo ""
echo "Test 7: Verifying Docker image..."
if docker images | grep -q "receipt-extractor-test"; then
    echo -e "${GREEN}✓${NC} Docker image receipt-extractor-test exists"
else
    echo -e "${YELLOW}⚠${NC}  Docker image not found (run: docker build -t receipt-extractor-test .)"
fi

# Summary
echo ""
echo "================================================================================"
echo "VALIDATION SUMMARY"
echo "================================================================================"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All validation tests passed!${NC}"
    echo ""
    echo "The Docker PORT environment variable fix is complete and validated."
    echo ""
    echo "Next steps:"
    echo "  1. Deploy to Railway/Koyeb"
    echo "  2. Monitor startup logs for port binding"
    echo "  3. Verify health endpoint accessibility"
    echo ""
    exit 0
else
    echo -e "${RED}✗ $ERRORS validation test(s) failed${NC}"
    echo ""
    echo "Please review the errors above and fix them before deploying."
    echo ""
    exit 1
fi
