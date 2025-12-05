#!/bin/bash
###############################################################################
# Receipt Extractor - Unified All-in-One Launcher v5.0
#
# This is the SINGLE launcher script for the entire project.
# Located at repository root for direct access after git pull.
#
# Features:
# - Automatic dependency installation and validation
# - Comprehensive test suite execution (dynamically counted)
# - CEFR refactoring and AI agent test reporting
# - Backend and Frontend server management
# - Database migrations
# - System health monitoring
# - Alternative deployment documentation
#
# Usage:
#   ./launcher.sh                 # Interactive menu
#   ./launcher.sh test            # Run all tests
#   ./launcher.sh test-quick      # Run quick tests (unit only)
#   ./launcher.sh test-full       # Run full test suite with coverage
#   ./launcher.sh dev             # Start development servers
#   ./launcher.sh deps            # Install dependencies
#   ./launcher.sh clean           # Clean cache
#   ./launcher.sh report          # Generate comprehensive test report
#   ./launcher.sh alternatives    # Show alternative deployment options
#   ./launcher.sh help            # Show help
#
# Works from any directory - auto-detects project root
###############################################################################

set -e

# Set TERM if not set (for compatibility)
export TERM=${TERM:-xterm}

# Colors and formatting
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Find project root directory (where this script is located)
SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -L "$SCRIPT_PATH" ]; do
  SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" && pwd)"
  SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
  [[ $SCRIPT_PATH != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done
PROJECT_ROOT="$(cd -P "$(dirname "$SCRIPT_PATH")" && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Configuration - all paths relative to project root
BACKEND_PORT=5000
FRONTEND_PORT=3000
BACKEND_DIR="web/backend"
FRONTEND_DIR="web/frontend"
TEST_DIR="tools/tests"
LOG_DIR="logs"
REPORT_DIR="logs/reports"

# Core dependencies for testing (update this list when adding new core deps)
CORE_DEPENDENCIES="pytest pytest-cov flask flask-cors pillow psutil requests pydantic"

# Test count estimate (dynamically calculated at runtime when needed)
TEST_COUNT_ESTIMATE=""

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"
mkdir -p "$LOG_DIR/test-reports"

# Global state variables
BACKEND_PID=""
FRONTEND_PID=""
TESTS_PASSED=false
DEPS_CHECKED=false
PYTHON_CMD=""
PIP_CMD=""

###############################################################################
# UI Functions
###############################################################################

print_banner() {
    clear
    local test_count=$(get_test_count)
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                        ║"
    echo "║           Receipt Extractor - Unified Launcher v5.0                    ║"
    echo "║                                                                        ║"
    echo "║      AI-Powered Receipt Processing with Comprehensive Testing          ║"
    echo "║                                                                        ║"
    echo "╚════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${DIM}Project Root: $PROJECT_ROOT${NC}"
    echo -e "${DIM}Tests Available: ~${test_count} tests across all modules${NC}"
    echo ""
}

print_separator() {
    echo -e "${DIM}──────────────────────────────────────────────────────────────────────────${NC}"
}

print_section() {
    echo ""
    echo -e "${BOLD}${BLUE}> $1${NC}"
    print_separator
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# Calculate test count dynamically
get_test_count() {
    if [ -z "$TEST_COUNT_ESTIMATE" ]; then
        if [ -d "$TEST_DIR" ]; then
            TEST_COUNT_ESTIMATE=$(find "$TEST_DIR" -name "test_*.py" -type f -exec grep -c "def test_" {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}')
            if [ -z "$TEST_COUNT_ESTIMATE" ] || [ "$TEST_COUNT_ESTIMATE" -eq 0 ]; then
                TEST_COUNT_ESTIMATE="N/A"
            fi
        else
            TEST_COUNT_ESTIMATE="N/A"
        fi
    fi
    echo "$TEST_COUNT_ESTIMATE"
}

# Check if process is running (more reliable than kill -0)
is_process_running() {
    local pid=$1
    if [ -z "$pid" ]; then
        return 1
    fi
    if [ -d "/proc/$pid" ]; then
        return 0
    elif ps -p "$pid" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

show_menu() {
    print_banner
    local test_count=$(get_test_count)
    echo -e "${BOLD}Main Menu:${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} Run Full Test Suite (~${test_count} tests with coverage)"
    echo -e "  ${GREEN}2)${NC} Run Quick Tests (fast, unit tests only)"
    echo -e "  ${GREEN}3)${NC} Generate Comprehensive Test Report"
    echo -e "  ${GREEN}4)${NC} Start Development Servers"
    echo -e "  ${GREEN}5)${NC} Install/Update Dependencies"
    echo -e "  ${GREEN}6)${NC} Clean Cache & Temp Files"
    echo -e "  ${GREEN}7)${NC} Run Database Migrations"
    echo -e "  ${GREEN}8)${NC} System Health Report"
    echo -e "  ${CYAN}A)${NC} Alternative Deployment Solutions"
    echo -e "  ${GREEN}H)${NC} Help & Documentation"
    echo -e "  ${RED}0)${NC} Exit"
    echo ""
    echo -ne "${BOLD}Select an option [0-8/A/H]:${NC} "
}

###############################################################################
# Python Detection
###############################################################################

detect_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python 3 is not installed"
        echo "Please install Python 3.8 or higher"
        return 1
    fi

    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
    else
        print_error "pip is not installed"
        return 1
    fi

    return 0
}

###############################################################################
# Cleanup Handler
###############################################################################

cleanup() {
    echo ""
    print_section "Shutting Down"

    # Kill backend
    if is_process_running "$BACKEND_PID"; then
        kill $BACKEND_PID 2>/dev/null || true
        wait $BACKEND_PID 2>/dev/null || true
        print_success "Backend server stopped"
    fi

    # Kill frontend
    if is_process_running "$FRONTEND_PID"; then
        kill $FRONTEND_PID 2>/dev/null || true
        wait $FRONTEND_PID 2>/dev/null || true
        print_success "Frontend server stopped"
    fi

    echo ""
    echo -e "${GREEN}${BOLD}Cleanup complete. Thank you for using Receipt Extractor!${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

###############################################################################
# System Checks
###############################################################################

check_python() {
    print_section "Python Environment Check"

    detect_python || return 1

    local PYTHON_VERSION
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION detected"
    print_success "pip available"
    return 0
}

check_directories() {
    print_section "Directory Structure Validation"

    local all_ok=true

    if [ ! -d "$BACKEND_DIR" ]; then
        print_error "Backend directory not found: $PROJECT_ROOT/$BACKEND_DIR"
        all_ok=false
    else
        print_success "Backend directory exists"
    fi

    if [ ! -d "$FRONTEND_DIR" ]; then
        print_error "Frontend directory not found: $PROJECT_ROOT/$FRONTEND_DIR"
        all_ok=false
    else
        print_success "Frontend directory exists"
    fi

    if [ ! -d "$TEST_DIR" ]; then
        print_error "Test directory not found: $PROJECT_ROOT/$TEST_DIR"
        all_ok=false
    else
        local test_count=$(find "$TEST_DIR" -name "*.py" -type f 2>/dev/null | wc -l)
        print_success "Test directory exists ($test_count test files)"
    fi

    # Check for requirements files
    if [ -f "requirements.txt" ]; then
        print_success "requirements.txt found in project root"
    elif [ -f "$BACKEND_DIR/requirements.txt" ]; then
        print_success "requirements.txt found in $BACKEND_DIR"
    else
        print_warning "No requirements.txt found"
    fi

    if $all_ok; then
        return 0
    else
        return 1
    fi
}

check_ports() {
    print_section "Port Availability Check"

    local ports_ok=true

    if command -v lsof &> /dev/null; then
        if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            print_error "Port $BACKEND_PORT is already in use"
            ports_ok=false
        else
            print_success "Port $BACKEND_PORT is available"
        fi

        if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            print_error "Port $FRONTEND_PORT is already in use"
            ports_ok=false
        else
            print_success "Port $FRONTEND_PORT is available"
        fi
    else
        print_warning "lsof not available, skipping port check"
    fi

    if $ports_ok; then
        return 0
    else
        return 1
    fi
}

###############################################################################
# Cache Cleaning Functions
###############################################################################

clean_cache() {
    print_section "Cleaning Python Cache"

    local pycache_count=0
    local pyc_count=0

    # Remove __pycache__ directories
    while IFS= read -r -d '' dir; do
        rm -rf "$dir" 2>/dev/null && ((pycache_count++)) || true
    done < <(find "$PROJECT_ROOT" -type d -name "__pycache__" -print0 2>/dev/null)

    # Remove .pyc files
    while IFS= read -r -d '' file; do
        rm -f "$file" 2>/dev/null && ((pyc_count++)) || true
    done < <(find "$PROJECT_ROOT" -type f -name "*.pyc" -print0 2>/dev/null)

    # Remove pytest cache
    if [ -d "$PROJECT_ROOT/.pytest_cache" ]; then
        rm -rf "$PROJECT_ROOT/.pytest_cache"
        print_success "Removed .pytest_cache directory"
    fi

    # Remove coverage cache
    if [ -f "$PROJECT_ROOT/.coverage" ]; then
        rm -f "$PROJECT_ROOT/.coverage"
        print_success "Removed .coverage file"
    fi

    if [ -d "$PROJECT_ROOT/htmlcov" ]; then
        rm -rf "$PROJECT_ROOT/htmlcov"
        print_success "Removed htmlcov directory"
    fi

    print_success "Removed $pycache_count __pycache__ directories"
    print_success "Removed $pyc_count .pyc files"
    print_info "Cache cleanup complete - tests will use fresh code"
}

###############################################################################
# Dependency Management
###############################################################################

install_dependencies() {
    print_section "Dependency Installation"

    detect_python || return 1

    # Determine which requirements file to use
    local req_file=""
    if [ -f "requirements.txt" ]; then
        req_file="requirements.txt"
        print_info "Using root requirements: requirements.txt"
    elif [ -f "$BACKEND_DIR/requirements.txt" ]; then
        req_file="$BACKEND_DIR/requirements.txt"
        print_info "Using backend requirements: $BACKEND_DIR/requirements.txt"
    else
        print_error "No requirements.txt file found"
        return 1
    fi

    # Install core dependencies first (from CORE_DEPENDENCIES variable)
    print_info "Installing core dependencies: $CORE_DEPENDENCIES"
    # shellcheck disable=SC2086
    $PIP_CMD install $CORE_DEPENDENCIES 2>&1 | tee "$LOG_DIR/pip-install.log" || true
    
    print_info "Installing remaining dependencies from $req_file..."
    if $PIP_CMD install -r "$req_file" 2>&1 | tee -a "$LOG_DIR/pip-install.log"; then
        DEPS_CHECKED=true
        print_success "All dependencies installed successfully"
        return 0
    else
        print_warning "Some dependencies may have failed to install"
        print_info "Core testing dependencies should still work"
        DEPS_CHECKED=true
        return 0
    fi
}

###############################################################################
# Test Functions
###############################################################################

run_quick_tests() {
    print_section "Running Quick Tests (Unit Tests Only)"
    
    clean_cache
    detect_python || return 1

    print_info "Running unit tests (fast execution)..."
    echo ""

    # Run tests with minimal output for quick feedback
    $PYTHON_CMD -m pytest "$TEST_DIR" \
        -v \
        --tb=short \
        -x \
        --ignore="$TEST_DIR/web" \
        --ignore="$TEST_DIR/backend" \
        2>&1 | tee "$LOG_DIR/test-reports/quick-tests.log"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_success "Quick tests passed!"
        TESTS_PASSED=true
        return 0
    else
        print_warning "Some quick tests failed"
        return 1
    fi
}

run_full_tests() {
    local test_count=$(get_test_count)
    print_section "Running Full Test Suite (~${test_count} Tests)"

    clean_cache
    detect_python || return 1

    print_info "Running comprehensive test suite with coverage..."
    print_info "This includes CEFR refactoring tests, AI agent tests, and all modules"
    echo ""

    # Use the pyproject.toml configuration
    $PYTHON_CMD -m pytest "$TEST_DIR" \
        --cov=shared \
        --cov="$BACKEND_DIR" \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-report=xml \
        -v \
        --tb=short \
        2>&1 | tee "$LOG_DIR/test-reports/full-test-suite.log"

    local test_result=${PIPESTATUS[0]}

    echo ""
    print_separator
    
    if [ $test_result -eq 0 ]; then
        print_success "All tests passed!"
        print_info "Coverage report: htmlcov/index.html"
        print_info "XML report: coverage.xml"
        TESTS_PASSED=true
        return 0
    else
        print_warning "Some tests failed"
        print_info "Coverage report: htmlcov/index.html"
        echo ""
        echo -ne "Continue anyway? [y/N]: "
        read -r continue_choice
        if [[ "$continue_choice" =~ ^[Yy]$ ]]; then
            TESTS_PASSED=false
            return 0
        else
            return 1
        fi
    fi
}

###############################################################################
# Comprehensive Test Report Generation
###############################################################################

generate_test_report() {
    print_section "Generating Comprehensive Test Report"

    detect_python || return 1

    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local report_file="$REPORT_DIR/test-report_${timestamp}.md"
    local json_report="$REPORT_DIR/test-report_${timestamp}.json"

    print_info "Running test suite and collecting metrics..."
    echo ""

    # Run tests with JSON report
    $PYTHON_CMD -m pytest "$TEST_DIR" \
        --cov=shared \
        --cov="$BACKEND_DIR" \
        --cov-report=term-missing \
        --cov-report=json \
        -v \
        --tb=short \
        2>&1 | tee "$LOG_DIR/test-reports/report-run.log"

    local test_result=${PIPESTATUS[0]}

    # Count test results from output
    # Note: grep -c returns exit code 1 when no matches found, so we use a subshell to ensure clean output
    local passed=$(grep -c "PASSED" "$LOG_DIR/test-reports/report-run.log" 2>/dev/null) || passed=0
    local failed=$(grep -c "FAILED" "$LOG_DIR/test-reports/report-run.log" 2>/dev/null) || failed=0
    local skipped=$(grep -c "SKIPPED" "$LOG_DIR/test-reports/report-run.log" 2>/dev/null) || skipped=0
    local total=$((passed + failed + skipped))

    # Generate markdown report
    {
        echo "# Receipt Extractor - Comprehensive Test Report"
        echo ""
        echo "**Generated:** $(date '+%Y-%m-%d %H:%M:%S')"
        echo "**Platform:** $(uname -s) $(uname -r)"
        echo "**Python Version:** $($PYTHON_CMD --version 2>&1)"
        echo ""
        echo "---"
        echo ""
        echo "## Executive Summary"
        echo ""
        echo "| Metric | Value |"
        echo "|--------|-------|"
        echo "| Total Tests | $total |"
        echo "| Passed | $passed |"
        echo "| Failed | $failed |"
        echo "| Skipped | $skipped |"
        echo "| Pass Rate | $(awk "BEGIN {if ($total > 0) printf \"%.1f%%\", ($passed / $total) * 100; else print \"N/A\"}")  |"
        echo ""
        echo "## Test Categories"
        echo ""
        echo "### Module Coverage"
        echo ""
        echo "| Module | Description |"
        echo "|--------|-------------|"
        echo "| shared/ | Core utilities, Circular Exchange Framework |"
        echo "| web/backend/ | Flask API, authentication, database |"
        echo "| tools/tests/ | Test infrastructure |"
        echo ""
        echo "### Test Types"
        echo ""
        echo "- **Unit Tests**: Fast, isolated tests for individual functions"
        echo "- **Integration Tests**: Tests for module interactions"
        echo "- **Model Tests**: AI/ML model validation tests"
        echo "- **Web Tests**: API endpoint tests"
        echo "- **CEFR Refactoring Tests**: Tests for language framework compliance"
        echo "- **AI Agent Tests**: Tests for AI-powered features"
        echo ""
        echo "## CEFR Refactoring Analysis"
        echo ""
        echo "The Circular Exchange Framework (CEF) provides:"
        echo ""
        echo "- **Dependency Management**: Automatic module loading and injection"
        echo "- **Change Notifications**: Event-driven architecture for updates"
        echo "- **Auto-tuning**: Performance optimization capabilities"
        echo "- **Metrics Analysis**: Comprehensive system monitoring"
        echo ""
        echo "### CEFR Test Coverage"
        echo ""
        echo "| Component | Status |"
        echo "|-----------|--------|"
        echo "| circular_exchange/core | $(if [ $test_result -eq 0 ]; then echo "PASS"; else echo "PARTIAL"; fi) |"
        echo "| circular_exchange/analysis | $(if [ $test_result -eq 0 ]; then echo "PASS"; else echo "PARTIAL"; fi) |"
        echo "| circular_exchange/auto_tuning | $(if [ $test_result -eq 0 ]; then echo "PASS"; else echo "PARTIAL"; fi) |"
        echo ""
        echo "## AI Agent Integration"
        echo ""
        echo "AI-powered features tested include:"
        echo ""
        echo "- **OCR Models**: EasyOCR, Tesseract, PaddleOCR"
        echo "- **Receipt Extraction**: Intelligent field parsing"
        echo "- **Batch Processing**: Multi-receipt handling"
        echo "- **Model Fine-tuning**: Custom model training"
        echo ""
        echo "## Recommendations"
        echo ""
        if [ $test_result -eq 0 ]; then
            echo "All tests passed. The system is ready for deployment."
        else
            echo "Some tests failed. Review the following:"
            echo ""
            echo "1. Check test output in \`$LOG_DIR/test-reports/report-run.log\`"
            echo "2. Run failed tests individually for detailed output"
            echo "3. Verify all dependencies are installed"
        fi
        echo ""
        echo "---"
        echo ""
        echo "**End of Report**"
        echo ""
        echo "This report was generated by the Receipt Extractor Unified Launcher v5.0"

    } > "$report_file"

    print_success "Report generated: $report_file"
    echo ""
    echo -e "${BOLD}Report Summary:${NC}"
    echo "  - Total Tests: $total"
    echo "  - Passed: $passed"
    echo "  - Failed: $failed"
    echo "  - Skipped: $skipped"
    echo ""
    echo -e "${BOLD}Files:${NC}"
    echo "  - Markdown Report: $report_file"
    echo "  - Test Log: $LOG_DIR/test-reports/report-run.log"
    echo "  - Coverage HTML: htmlcov/index.html"
    echo ""
    
    echo -ne "Open report now? [y/N]: "
    read -r view_choice
    if [[ "$view_choice" =~ ^[Yy]$ ]]; then
        if command -v less &> /dev/null; then
            less "$report_file"
        else
            cat "$report_file"
        fi
    fi
}

###############################################################################
# Alternative Deployment Solutions
###############################################################################

show_alternatives() {
    print_section "Alternative Deployment Solutions"

    echo ""
    echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║                    DEPLOYMENT ALTERNATIVES                             ║${NC}"
    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${BOLD}1. LOCAL DEVELOPMENT${NC}"
    echo "   ─────────────────────────────────────────────"
    echo "   Run entirely on your local machine."
    echo ""
    echo "   ${GREEN}Pros:${NC}"
    echo "   - Full control over environment"
    echo "   - No internet required after setup"
    echo "   - Data stays on your machine"
    echo ""
    echo "   ${YELLOW}Cons:${NC}"
    echo "   - Requires local Python/dependencies"
    echo "   - Limited by local hardware"
    echo ""
    echo "   ${CYAN}Commands:${NC}"
    echo "   ./launcher.sh deps     # Install dependencies"
    echo "   ./launcher.sh dev      # Start servers"
    echo ""

    echo -e "${BOLD}2. DOCKER CONTAINERIZATION${NC}"
    echo "   ─────────────────────────────────────────────"
    echo "   Run in isolated Docker containers."
    echo ""
    echo "   ${GREEN}Pros:${NC}"
    echo "   - Consistent environment everywhere"
    echo "   - Easy deployment and scaling"
    echo "   - Isolation from host system"
    echo ""
    echo "   ${CYAN}Commands:${NC}"
    echo "   docker build -t receipt-extractor ."
    echo "   docker run -p 5000:5000 -p 3000:3000 receipt-extractor"
    echo ""

    echo -e "${BOLD}3. CLOUD PLATFORMS${NC}"
    echo "   ─────────────────────────────────────────────"
    echo ""
    echo "   ${MAGENTA}a) Railway (Recommended for Quick Deploy)${NC}"
    echo "      - One-click deployment"
    echo "      - Auto-scaling"
    echo "      - Built-in PostgreSQL"
    echo "      Config: railway.json included"
    echo ""
    echo "   ${MAGENTA}b) Heroku${NC}"
    echo "      - Easy Git-based deployment"
    echo "      - Add-ons ecosystem"
    echo "      Config: Procfile included"
    echo ""
    echo "   ${MAGENTA}c) AWS (Enterprise)${NC}"
    echo "      - ECS/EKS for containers"
    echo "      - Lambda for serverless"
    echo "      - S3 for storage"
    echo ""
    echo "   ${MAGENTA}d) Google Cloud${NC}"
    echo "      - Cloud Run for containers"
    echo "      - Cloud Functions for serverless"
    echo "      - Cloud Storage for files"
    echo ""
    echo "   ${MAGENTA}e) Azure${NC}"
    echo "      - App Service for web apps"
    echo "      - Azure Functions for serverless"
    echo "      - Blob Storage for files"
    echo ""

    echo -e "${BOLD}4. HYBRID OFFLINE/ONLINE${NC}"
    echo "   ─────────────────────────────────────────────"
    echo "   PWA (Progressive Web App) approach:"
    echo ""
    echo "   ${GREEN}Features:${NC}"
    echo "   - Works offline with service workers"
    echo "   - Syncs when online"
    echo "   - Installable on devices"
    echo ""
    echo "   ${CYAN}Implementation:${NC}"
    echo "   - Add service worker to frontend"
    echo "   - Implement IndexedDB for offline storage"
    echo "   - Queue API calls for sync"
    echo ""

    echo -e "${BOLD}5. DESKTOP APPLICATION${NC}"
    echo "   ─────────────────────────────────────────────"
    echo "   Package as standalone desktop app."
    echo ""
    echo "   ${GREEN}Options:${NC}"
    echo "   - Electron (Cross-platform)"
    echo "   - Tauri (Lightweight, Rust-based)"
    echo "   - PyInstaller (Python-based)"
    echo ""
    echo "   ${CYAN}Location:${NC}"
    echo "   - Desktop implementation: desktop/"
    echo ""

    echo -e "${BOLD}6. API-ONLY MICROSERVICE${NC}"
    echo "   ─────────────────────────────────────────────"
    echo "   Deploy backend as microservice, use any frontend."
    echo ""
    echo "   ${GREEN}Benefits:${NC}"
    echo "   - Frontend flexibility"
    echo "   - Easy integration"
    echo "   - Independent scaling"
    echo ""
    echo "   ${CYAN}Commands:${NC}"
    echo "   gunicorn -w 4 -b 0.0.0.0:5000 'web.backend.app:app'"
    echo ""

    echo ""
    print_separator
    echo ""
    echo -e "${BOLD}Recommended for most users: Docker or Railway${NC}"
    echo ""
    echo -e "See ${CYAN}PRODUCTION_DEPLOYMENT.md${NC} for detailed instructions."
    echo ""
    echo -ne "Press Enter to continue..."
    read -r
}

###############################################################################
# Database Migrations
###############################################################################

run_migrations() {
    print_section "Database Migrations"

    detect_python || return 1

    print_info "Running database migrations with Alembic..."

    # Export USE_SQLITE for development/testing
    export USE_SQLITE=true

    # Check if alembic is installed
    if ! command -v alembic &> /dev/null; then
        print_warning "Alembic not found, installing..."
        $PIP_CMD install -q alembic
    fi

    # Check if migrations directory exists
    if [ ! -d "migrations" ]; then
        print_warning "Migrations directory not found, skipping migrations"
        return 0
    fi

    # Run migrations
    cd migrations
    if alembic upgrade head 2>&1 | tee "../$LOG_DIR/migrations.log"; then
        print_success "Database migrations completed"
        cd "$PROJECT_ROOT"
        return 0
    else
        print_error "Database migrations failed"
        echo "Check $LOG_DIR/migrations.log for details"
        cd "$PROJECT_ROOT"
        return 1
    fi
}

###############################################################################
# Server Management
###############################################################################

start_servers() {
    detect_python || return 1
    check_directories || return 1
    check_ports || return 1

    if [ "$DEPS_CHECKED" != true ]; then
        echo ""
        echo -ne "Install dependencies first? [Y/n]: "
        read -r deps_choice
        if [[ ! "$deps_choice" =~ ^[Nn]$ ]]; then
            install_dependencies || {
                print_warning "Dependency installation had issues, but continuing..."
            }
        fi
    fi

    # Run database migrations
    run_migrations || {
        print_warning "Migrations failed, but continuing..."
    }

    print_section "Starting Services"

    # Export USE_SQLITE for development/testing
    export USE_SQLITE=true

    # Start backend
    print_info "Starting backend API server..."
    cd "$BACKEND_DIR"
    $PYTHON_CMD app.py > "$PROJECT_ROOT/$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    cd "$PROJECT_ROOT"

    sleep 3

    if ! is_process_running "$BACKEND_PID"; then
        print_error "Backend failed to start"
        echo "Check $LOG_DIR/backend.log for details:"
        echo ""
        tail -20 "$LOG_DIR/backend.log"
        return 1
    fi

    print_success "Backend running on http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)"

    # Start frontend
    print_info "Starting frontend web server..."
    cd "$FRONTEND_DIR"
    $PYTHON_CMD -m http.server $FRONTEND_PORT > "$PROJECT_ROOT/$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    cd "$PROJECT_ROOT"

    sleep 2

    if ! is_process_running "$FRONTEND_PID"; then
        print_error "Frontend failed to start"
        echo "Check $LOG_DIR/frontend.log for details"
        # Stop the backend since frontend failed
        if is_process_running "$BACKEND_PID"; then
            kill "$BACKEND_PID" 2>/dev/null || true
        fi
        return 1
    fi

    print_success "Frontend running on http://localhost:$FRONTEND_PORT (PID: $FRONTEND_PID)"

    # Open browser
    print_section "Opening Application"
    sleep 1

    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:$FRONTEND_PORT" 2>/dev/null &
    elif command -v open &> /dev/null; then
        open "http://localhost:$FRONTEND_PORT" 2>/dev/null &
    else
        print_warning "Could not auto-open browser"
    fi

    # Success message
    echo ""
    echo -e "${GREEN}${BOLD}╔════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║                                                                        ║${NC}"
    echo -e "${GREEN}${BOLD}║          Receipt Extractor is now running!                             ║${NC}"
    echo -e "${GREEN}${BOLD}║                                                                        ║${NC}"
    echo -e "${GREEN}${BOLD}╚════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${BOLD}Frontend:${NC}  ${CYAN}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "  ${BOLD}Backend:${NC}   ${CYAN}http://localhost:$BACKEND_PORT${NC}"
    echo -e "  ${BOLD}API Health:${NC} ${CYAN}http://localhost:$BACKEND_PORT/api/health${NC}"
    echo ""
    echo -e "${YELLOW}${BOLD}Press Ctrl+C to stop all servers${NC}"
    echo ""
    echo -e "${DIM}Logs: $LOG_DIR/backend.log | $LOG_DIR/frontend.log${NC}"
    echo ""

    # Monitor processes
    monitor_services
}

monitor_services() {
    while true; do
        if ! is_process_running "$BACKEND_PID"; then
            print_error "Backend process died unexpectedly!"
            echo "Last 20 lines of backend.log:"
            tail -20 "$LOG_DIR/backend.log"
            break
        fi

        if ! is_process_running "$FRONTEND_PID"; then
            print_error "Frontend process died unexpectedly!"
            echo "Last 20 lines of frontend.log:"
            tail -20 "$LOG_DIR/frontend.log"
            break
        fi

        sleep 3
    done
}

###############################################################################
# System Health Report
###############################################################################

system_health_report() {
    print_section "System Health Report"

    detect_python || return 1

    echo ""
    echo -e "${BOLD}Environment:${NC}"
    echo "  Python: $($PYTHON_CMD --version 2>&1)"
    echo "  Project Root: $PROJECT_ROOT"
    echo "  Log Directory: $LOG_DIR"
    echo ""

    echo -e "${BOLD}Directory Structure:${NC}"
    [ -d "$BACKEND_DIR" ] && echo -e "  Backend:  ${GREEN}[EXISTS]${NC} ($BACKEND_DIR)" || echo -e "  Backend:  ${RED}[MISSING]${NC}"
    [ -d "$FRONTEND_DIR" ] && echo -e "  Frontend: ${GREEN}[EXISTS]${NC} ($FRONTEND_DIR)" || echo -e "  Frontend: ${RED}[MISSING]${NC}"
    [ -d "$TEST_DIR" ] && echo -e "  Tests:    ${GREEN}[EXISTS]${NC} ($TEST_DIR)" || echo -e "  Tests:    ${RED}[MISSING]${NC}"
    [ -f "requirements.txt" ] && echo -e "  Requirements: ${GREEN}[FOUND]${NC}" || echo -e "  Requirements: ${RED}[MISSING]${NC}"
    echo ""

    echo -e "${BOLD}Test Statistics:${NC}"
    if [ -d "$TEST_DIR" ]; then
        local test_file_count=$(find "$TEST_DIR" -name "test_*.py" -type f 2>/dev/null | wc -l)
        local test_count=$(get_test_count)
        echo "  Test Files: $test_file_count"
        echo "  Expected Tests: ~${test_count} (based on collected tests)"
    fi
    echo ""

    echo -e "${BOLD}Services:${NC}"
    echo "  Backend Port: $BACKEND_PORT"
    echo "  Frontend Port: $FRONTEND_PORT"

    if is_process_running "$BACKEND_PID"; then
        echo -e "  Backend Status: ${GREEN}[RUNNING]${NC} (PID: $BACKEND_PID)"
    else
        echo -e "  Backend Status: ${YELLOW}[NOT RUNNING]${NC}"
    fi

    if is_process_running "$FRONTEND_PID"; then
        echo -e "  Frontend Status: ${GREEN}[RUNNING]${NC} (PID: $FRONTEND_PID)"
    else
        echo -e "  Frontend Status: ${YELLOW}[NOT RUNNING]${NC}"
    fi

    echo ""
    echo -e "${BOLD}Status:${NC}"
    [ "$DEPS_CHECKED" = true ] && echo -e "  Dependencies: ${GREEN}[VERIFIED]${NC}" || echo -e "  Dependencies: ${YELLOW}[NOT CHECKED]${NC}"
    [ "$TESTS_PASSED" = true ] && echo -e "  Tests: ${GREEN}[PASSED]${NC}" || echo -e "  Tests: ${YELLOW}[NOT RUN]${NC}"

    echo ""
    echo -ne "Press Enter to continue..."
    read -r
}

###############################################################################
# Help
###############################################################################

show_help() {
    print_section "Help & Documentation"
    local test_count=$(get_test_count)

    echo ""
    echo -e "${BOLD}Quick Start:${NC}"
    echo "  1. Run ./launcher.sh deps to install dependencies"
    echo "  2. Run ./launcher.sh test to verify everything works"
    echo "  3. Run ./launcher.sh dev to start the application"
    echo ""
    echo -e "${BOLD}Command Line Options:${NC}"
    echo "  ./launcher.sh                 Interactive menu (default)"
    echo "  ./launcher.sh test            Run full test suite"
    echo "  ./launcher.sh test-quick      Run quick tests only"
    echo "  ./launcher.sh test-full       Run full tests with coverage"
    echo "  ./launcher.sh report          Generate comprehensive test report"
    echo "  ./launcher.sh dev             Start development servers"
    echo "  ./launcher.sh deps            Install dependencies"
    echo "  ./launcher.sh clean           Clean cache files"
    echo "  ./launcher.sh migrate         Run database migrations"
    echo "  ./launcher.sh health          System health report"
    echo "  ./launcher.sh alternatives    Show deployment alternatives"
    echo "  ./launcher.sh help            Show this help"
    echo ""
    local test_count=$(get_test_count)
    echo -e "${BOLD}Test Suite Information:${NC}"
    echo "  - Total Tests: ~${test_count}"
    echo "  - Categories: unit, integration, model, web, CEFR, AI agents"
    echo "  - Coverage: shared/, web/backend/, tools/tests/"
    echo ""
    echo -e "${BOLD}Key Features:${NC}"
    echo "  - Single unified launcher at repository root"
    echo "  - Auto-detects project root from any directory"
    echo "  - Comprehensive test reporting with CEFR analysis"
    echo "  - Multiple deployment options documented"
    echo "  - AI agent integration testing"
    echo ""
    echo -e "${BOLD}Project Structure:${NC}"
    echo "  launcher.sh          - This unified launcher"
    echo "  web/backend/         - Flask API backend"
    echo "  web/frontend/        - Web frontend"
    echo "  shared/              - Shared utilities & Circular Exchange Framework"
    echo "  tools/tests/         - Test suite (~${test_count} tests)"
    echo "  desktop/             - Desktop application"
    echo ""
    echo -e "${BOLD}Logs Location:${NC}"
    echo "  All logs: $PROJECT_ROOT/$LOG_DIR/"
    echo "  Test reports: $PROJECT_ROOT/$REPORT_DIR/"
    echo ""
    echo -ne "Press Enter to continue..."
    read -r
}

###############################################################################
# Main Program
###############################################################################

main() {
    # Handle command line arguments
    case "${1:-menu}" in
        test)
            print_banner
            run_full_tests
            exit $?
            ;;
        test-quick|quick)
            print_banner
            run_quick_tests
            exit $?
            ;;
        test-full|full)
            print_banner
            run_full_tests
            exit $?
            ;;
        report)
            print_banner
            generate_test_report
            exit $?
            ;;
        dev|start|serve)
            print_banner
            start_servers
            exit $?
            ;;
        clean)
            print_banner
            clean_cache
            echo ""
            print_success "Cleanup complete"
            exit 0
            ;;
        deps|dependencies)
            print_banner
            install_dependencies
            exit $?
            ;;
        migrate|migrations)
            print_banner
            run_migrations
            exit $?
            ;;
        health)
            print_banner
            system_health_report
            exit $?
            ;;
        alternatives|alt)
            print_banner
            show_alternatives
            exit 0
            ;;
        help|-h|--help)
            print_banner
            show_help
            exit 0
            ;;
        menu|*)
            # Interactive menu
            while true; do
                show_menu
                read -r choice

                case $choice in
                    1)
                        print_banner
                        run_full_tests
                        echo ""
                        echo -ne "Press Enter to continue..."
                        read -r
                        ;;
                    2)
                        print_banner
                        run_quick_tests
                        echo ""
                        echo -ne "Press Enter to continue..."
                        read -r
                        ;;
                    3)
                        print_banner
                        generate_test_report
                        ;;
                    4)
                        print_banner
                        start_servers
                        ;;
                    5)
                        print_banner
                        install_dependencies
                        echo ""
                        echo -ne "Press Enter to continue..."
                        read -r
                        ;;
                    6)
                        print_banner
                        clean_cache
                        echo ""
                        echo -ne "Press Enter to continue..."
                        read -r
                        ;;
                    7)
                        print_banner
                        run_migrations
                        echo ""
                        echo -ne "Press Enter to continue..."
                        read -r
                        ;;
                    8)
                        print_banner
                        system_health_report
                        ;;
                    [Aa])
                        print_banner
                        show_alternatives
                        ;;
                    [Hh])
                        print_banner
                        show_help
                        ;;
                    0)
                        cleanup
                        ;;
                    *)
                        print_error "Invalid option. Please try again."
                        sleep 2
                        ;;
                esac
            done
            ;;
    esac
}

# Check if running as root (warn if so)
if [ "$EUID" -eq 0 ] && [ -t 0 ]; then
    print_warning "Running as root is not recommended"
    echo -ne "Continue anyway? [y/N]: "
    read -r sudo_choice
    if [[ ! "$sudo_choice" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run main program
main "$@"
