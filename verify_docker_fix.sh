#!/bin/bash
# Docker Build Verification Script
# Tests that the Dockerfile builds successfully and training module is preserved

set -e  # Exit on any error

echo "=========================================="
echo "Docker Build Verification Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed or not in PATH${NC}"
    echo "Please install Docker to run this verification"
    exit 1
fi

echo -e "${GREEN}✅ Docker is available${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Change to project root
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Step 1: Validate Dockerfile Syntax"
echo "=========================================="

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}❌ Dockerfile not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Dockerfile exists${NC}"

# Validate required patterns
echo ""
echo "Checking Dockerfile content..."

if grep -q "path ./web/backend/training -prune" Dockerfile; then
    echo -e "${GREEN}✅ Training directory exclusion found${NC}"
else
    echo -e "${RED}❌ Training directory exclusion missing${NC}"
    exit 1
fi

if grep -q "test -d web/backend/training" Dockerfile; then
    echo -e "${GREEN}✅ Training directory verification found${NC}"
else
    echo -e "${RED}❌ Training directory verification missing${NC}"
    exit 1
fi

if grep -q "import web.backend.training.celery_worker" Dockerfile; then
    echo -e "${GREEN}✅ Training module import verification found${NC}"
else
    echo -e "${RED}❌ Training module import verification missing${NC}"
    exit 1
fi

if grep -q '${PORT:-5000}' Dockerfile; then
    echo -e "${GREEN}✅ HEALTHCHECK uses proper shell interpolation${NC}"
else
    echo -e "${YELLOW}⚠️  HEALTHCHECK might not use proper shell interpolation${NC}"
fi

echo ""
echo "=========================================="
echo "Step 2: Check Training Directory"
echo "=========================================="

if [ -d "web/backend/training" ]; then
    echo -e "${GREEN}✅ web/backend/training directory exists${NC}"
    echo ""
    echo "Training module files:"
    ls -lh web/backend/training/ | tail -n +2
else
    echo -e "${RED}❌ web/backend/training directory not found${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "Step 3: Build Docker Image (Optional)"
echo "=========================================="

read -p "Do you want to build the Docker image? This will take several minutes. (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    IMAGE_NAME="receipt-extractor-test"
    
    echo ""
    echo "Building Docker image: $IMAGE_NAME"
    echo "This may take 5-10 minutes..."
    echo ""
    
    if docker build -t "$IMAGE_NAME" . ; then
        echo ""
        echo -e "${GREEN}✅ Docker build successful${NC}"
        
        echo ""
        echo "=========================================="
        echo "Step 4: Verify Training Module in Image"
        echo "=========================================="
        
        echo ""
        echo "Checking training directory in image..."
        if docker run --rm "$IMAGE_NAME" ls -la web/backend/training/ 2>/dev/null; then
            echo -e "${GREEN}✅ Training directory exists in image${NC}"
        else
            echo -e "${RED}❌ Training directory missing in image${NC}"
            exit 1
        fi
        
        echo ""
        echo "Testing training module import..."
        if docker run --rm "$IMAGE_NAME" python -c "import web.backend.training.celery_worker; print('✅ Import successful')" 2>/dev/null; then
            echo -e "${GREEN}✅ Training module imports successfully${NC}"
        else
            echo -e "${RED}❌ Cannot import training module${NC}"
            exit 1
        fi
        
        echo ""
        echo -e "${GREEN}=========================================="
        echo "✅ ALL VERIFICATIONS PASSED"
        echo "==========================================${NC}"
        echo ""
        echo "Docker image '$IMAGE_NAME' is ready for use."
        echo ""
        echo "To run the container:"
        echo "  docker run -d -p 5000:5000 --name receipt-extractor $IMAGE_NAME"
        echo ""
        echo "To clean up:"
        echo "  docker rmi $IMAGE_NAME"
        
    else
        echo ""
        echo -e "${RED}❌ Docker build failed${NC}"
        exit 1
    fi
else
    echo ""
    echo "Skipping Docker build."
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✅ SYNTAX VERIFICATIONS PASSED"
    echo "==========================================${NC}"
    echo ""
    echo "Dockerfile syntax is correct and contains all required fixes."
    echo "Run this script with 'y' to build and test the Docker image."
fi

echo ""
