#!/bin/bash
# =============================================================================
# Health Check Script - Deployment Validation
# =============================================================================
# Validates critical modules and environment variables for deployment
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed
#
# Usage:
#   ./scripts/health_check.sh
#   bash scripts/health_check.sh
# =============================================================================

set -e

echo "=========================================="
echo "Deployment Health Check"
echo "=========================================="

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
ERRORS=0

# =============================================================================
# Check 1: Python modules
# =============================================================================
echo ""
echo "Checking Python modules..."

# Check training module
if python -c "import web.backend.training.celery_worker; print('✓ Training module OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ web.backend.training.celery_worker${NC}"
else
    echo -e "${RED}✗ web.backend.training.celery_worker - FAILED${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check Flask app
if python -c "import web.backend.app; print('✓ Flask app OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ web.backend.app${NC}"
else
    echo -e "${RED}✗ web.backend.app - FAILED${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check shared modules
if python -c "import shared.models.engine; print('✓ Models engine OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ shared.models.engine${NC}"
else
    echo -e "${RED}✗ shared.models.engine - FAILED${NC}"
    ERRORS=$((ERRORS + 1))
fi

# =============================================================================
# Check 2: Environment variables
# =============================================================================
echo ""
echo "Checking environment variables..."

# Check PORT variable
if [ -z "$PORT" ]; then
    echo -e "${YELLOW}⚠ Warning: PORT not set, using default 8000${NC}"
    export PORT=8000
else
    echo -e "${GREEN}✓ PORT=${PORT}${NC}"
fi

# Check JWT_SECRET (optional but recommended)
if [ -z "$JWT_SECRET" ]; then
    echo -e "${YELLOW}⚠ Warning: JWT_SECRET not set (using default)${NC}"
else
    echo -e "${GREEN}✓ JWT_SECRET is set${NC}"
fi

# Check REDIS_URL (optional for Celery)
if [ -z "$REDIS_URL" ]; then
    echo -e "${YELLOW}⚠ Info: REDIS_URL not set (Celery may not work)${NC}"
else
    echo -e "${GREEN}✓ REDIS_URL is set${NC}"
fi

# =============================================================================
# Check 3: Directory structure
# =============================================================================
echo ""
echo "Checking directory structure..."

REQUIRED_DIRS=(
    "web/backend"
    "web/backend/training"
    "web/frontend"
    "shared"
    "shared/models"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓ $dir exists${NC}"
    else
        echo -e "${RED}✗ $dir missing - FAILED${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

# =============================================================================
# Check 4: Critical files
# =============================================================================
echo ""
echo "Checking critical files..."

REQUIRED_FILES=(
    "web/backend/app.py"
    "web/backend/training/__init__.py"
    "web/backend/training/celery_worker.py"
    "shared/models/engine.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file exists${NC}"
    else
        echo -e "${RED}✗ $file missing - FAILED${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

# =============================================================================
# Check 5: Optional dependencies
# =============================================================================
echo ""
echo "Checking optional dependencies..."

# Check Celery
if python -c "import celery" 2>/dev/null; then
    echo -e "${GREEN}✓ Celery is installed${NC}"
else
    echo -e "${YELLOW}⚠ Celery not installed (background tasks disabled)${NC}"
fi

# Check Redis
if python -c "import redis" 2>/dev/null; then
    echo -e "${GREEN}✓ Redis client is installed${NC}"
else
    echo -e "${YELLOW}⚠ Redis client not installed (Celery disabled)${NC}"
fi

# =============================================================================
# Final status
# =============================================================================
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo "=========================================="
    exit 0
else
    echo -e "${RED}✗ Health check failed with $ERRORS error(s)${NC}"
    echo "=========================================="
    exit 1
fi
