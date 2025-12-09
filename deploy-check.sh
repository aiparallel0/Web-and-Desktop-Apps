#!/bin/bash

##############################################################################
# Receipt Extractor - Deployment Readiness Check
#
# This script validates that the project is ready for production deployment
# 
# Usage: ./deploy-check.sh
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                                                                    ║"
echo "║         Receipt Extractor - Deployment Readiness Check            ║"
echo "║                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

# Function to check if a file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $2"
        ((CHECKS_FAILED++))
        return 1
    fi
}

# Function to check if a command exists
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $2"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $2"
        ((WARNINGS++))
        return 1
    fi
}

echo ""
echo -e "${BLUE}📦 Checking Required Files...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_file "Procfile" "Procfile exists"
check_file "railway.json" "Railway config exists"
check_file "Dockerfile" "Dockerfile exists"
check_file "requirements.txt" "requirements.txt exists"
check_file ".env.example" ".env.example exists"
check_file "web/backend/app.py" "Main Flask app exists"
check_file "web/backend/billing/stripe_handler.py" "Stripe integration exists"
check_file "web/frontend/pricing.html" "Pricing page exists"

echo ""
echo -e "${BLUE}🔧 Checking System Dependencies...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_command "python3" "Python 3 installed"
check_command "pip" "pip installed"
check_command "git" "Git installed"

echo ""
echo -e "${BLUE}🧪 Checking Python Modules...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if virtual environment is recommended
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠${NC} No virtual environment detected (optional)"
    ((WARNINGS++))
else
    echo -e "${GREEN}✓${NC} Virtual environment active"
    ((CHECKS_PASSED++))
fi

# Check critical Python imports
echo "Checking Python imports..."
python3 -c "import flask" 2>/dev/null && echo -e "${GREEN}✓${NC} Flask installed" && ((CHECKS_PASSED++)) || (echo -e "${RED}✗${NC} Flask not installed" && ((CHECKS_FAILED++)))
python3 -c "import sqlalchemy" 2>/dev/null && echo -e "${GREEN}✓${NC} SQLAlchemy installed" && ((CHECKS_PASSED++)) || (echo -e "${RED}✗${NC} SQLAlchemy not installed" && ((CHECKS_FAILED++)))
python3 -c "import stripe" 2>/dev/null && echo -e "${GREEN}✓${NC} Stripe library installed" && ((CHECKS_PASSED++)) || (echo -e "${YELLOW}⚠${NC} Stripe library not installed (required for billing)" && ((WARNINGS++)))

echo ""
echo -e "${BLUE}📝 Checking Configuration...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if .env exists
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
    ((CHECKS_PASSED++))
    
    # Check critical environment variables
    if grep -q "STRIPE_SECRET_KEY" .env; then
        echo -e "${GREEN}✓${NC} Stripe keys configured in .env"
        ((CHECKS_PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} Stripe keys not found in .env"
        ((WARNINGS++))
    fi
    
    if grep -q "SENDGRID_API_KEY\|EMAIL_PROVIDER" .env; then
        echo -e "${GREEN}✓${NC} Email configuration found in .env"
        ((CHECKS_PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} Email configuration not found in .env"
        ((WARNINGS++))
    fi
    
    if grep -q "JWT_SECRET" .env; then
        echo -e "${GREEN}✓${NC} JWT secret configured in .env"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} JWT secret not configured in .env"
        ((CHECKS_FAILED++))
    fi
else
    echo -e "${YELLOW}⚠${NC} .env file not found (copy from .env.example)"
    ((WARNINGS++))
fi

echo ""
echo -e "${BLUE}🔍 Checking Code Quality...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for syntax errors
echo "Checking Python syntax..."
if python3 tools/scripts/validate_imports.py &> /dev/null; then
    echo -e "${GREEN}✓${NC} All Python files have valid syntax"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Syntax errors found (run: python3 tools/scripts/validate_imports.py)"
    ((CHECKS_FAILED++))
fi

# Check if tests exist
if [ -d "tools/tests" ]; then
    TEST_COUNT=$(find tools/tests -name "test_*.py" | wc -l)
    echo -e "${GREEN}✓${NC} Found $TEST_COUNT test files"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} No test directory found"
    ((WARNINGS++))
fi

echo ""
echo -e "${BLUE}🚀 Deployment Checklist...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Before deploying to production, ensure you have:"
echo ""
echo "[ ] Stripe account created and verified"
echo "[ ] SendGrid account created (or other email provider)"
echo "[ ] Domain name purchased (optional but recommended)"
echo "[ ] Railway account created"
echo "[ ] Production environment variables ready"
echo "[ ] Database migration script tested"
echo "[ ] Payment flow tested end-to-end"
echo ""

echo ""
echo -e "${BLUE}📊 Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Passed:${NC} $CHECKS_PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC} $CHECKS_FAILED"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Project is ready for deployment!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review QUICK_DEPLOY_GUIDE.md for deployment instructions"
    echo "2. Set up Stripe account (if not done)"
    echo "3. Set up SendGrid account (if not done)"
    echo "4. Deploy to Railway following the guide"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Please fix the failed checks before deploying${NC}"
    echo ""
    echo "Common fixes:"
    echo "- Install missing dependencies: pip install -r requirements.txt"
    echo "- Create .env file: cp .env.example .env"
    echo "- Fix syntax errors: python3 tools/scripts/validate_imports.py"
    echo ""
    exit 1
fi
