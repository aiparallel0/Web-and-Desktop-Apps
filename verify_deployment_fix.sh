#!/bin/bash
# Quick verification script to check if deployment fix is complete

echo "==================================="
echo "Deployment Fix Verification"
echo "==================================="
echo ""

# Check 1: Training module files exist
echo "✓ Checking training module files..."
for file in \
    "web/backend/training/__init__.py" \
    "web/backend/training/celery_worker.py" \
    "web/backend/training/base.py"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file exists"
    else
        echo "  ✗ $file MISSING"
        exit 1
    fi
done

# Check 2: Dockerfile doesn't delete training
echo ""
echo "✓ Checking Dockerfile..."
if grep -q "rm -rf web/backend/training" Dockerfile; then
    echo "  ✗ Dockerfile still deletes training directory!"
    exit 1
else
    echo "  ✓ Training directory preserved"
fi

# Check 3: PORT handling in Dockerfile
echo ""
echo "✓ Checking PORT handling..."
if grep -q "bind 0.0.0.0:\${PORT:-" Dockerfile; then
    echo "  ✓ Dockerfile uses proper PORT syntax with fallback"
else
    echo "  ⚠ Warning: PORT handling may need review"
fi

# Check 4: Procfile has Celery worker
echo ""
echo "✓ Checking Procfile..."
if grep -q "celery -A web.backend.training.celery_worker worker" Procfile; then
    echo "  ✓ Celery worker configured correctly"
else
    echo "  ✗ Celery worker configuration missing"
    exit 1
fi

# Check 5: Requirements have celery and redis
echo ""
echo "✓ Checking requirements..."
if grep -q "celery>=" requirements-prod.txt && grep -q "redis>=" requirements-prod.txt; then
    echo "  ✓ Celery and Redis in requirements-prod.txt"
else
    echo "  ✗ Missing Celery or Redis in requirements"
    exit 1
fi

echo ""
echo "==================================="
echo "✅ All verification checks passed!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Deploy to Railway/production environment"
echo "2. Monitor deployment logs for errors"
echo "3. Verify health endpoint: GET /api/health"
echo "4. Test Celery worker starts successfully"
echo ""
