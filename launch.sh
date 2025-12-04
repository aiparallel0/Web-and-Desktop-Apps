#!/bin/bash
###############################################################################
# Receipt Extractor - Unified Launcher Script (All-in-One)
#
# This script combines all launcher functionality with fixed paths and
# comprehensive features:
# - Automatic cache cleaning (Python bytecode, pytest cache)
# - Dependency checking and installation
# - Backend and Frontend server management
# - GPU detection
# - Test execution with coverage
# - Health monitoring and diagnostics
# - Database migrations
# - Performance metrics tracking
#
# Usage: ./launch.sh [option]
#   No option: Interactive menu
#   --quick: Quick launch (skip tests)
#   --test:  Run tests only
#   --clean: Clean cache only
#   --help:  Show help
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
REQUIREMENTS_FILE="requirements.txt"
BACKEND_REQUIREMENTS="$BACKEND_DIR/requirements.txt"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$LOG_DIR/test-reports"

# Global state variables
BACKEND_PID=""
FRONTEND_PID=""
TESTS_PASSED=false
DEPS_CHECKED=false
GPU_AVAILABLE=false

###############################################################################
# UI Functions
###############################################################################

print_banner() {
    clear
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                    ║"
    echo "║         Receipt Extractor - Unified Launcher v4.0                  ║"
    echo "║                                                                    ║"
    echo "║    AI-Powered Receipt Processing with Advanced OCR Models          ║"
    echo "║                                                                    ║"
    echo "╚════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${DIM}Project Root: $PROJECT_ROOT${NC}"
    echo ""
}

print_separator() {
    echo -e "${DIM}────────────────────────────────────────────────────────────────────${NC}"
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

show_menu() {
    print_banner
    echo -e "${BOLD}Main Menu:${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} Quick Launch (Skip Tests)"
    echo -e "  ${GREEN}2)${NC} Full Launch (With Tests & Validation)"
    echo -e "  ${GREEN}3)${NC} Run Tests Only"
    echo -e "  ${GREEN}4)${NC} Check & Install Dependencies"
    echo -e "  ${GREEN}5)${NC} System Health Report"
    echo -e "  ${GREEN}6)${NC} Clean Cache (Python bytecode & pytest)"
    echo -e "  ${GREEN}7)${NC} Run Database Migrations"
    echo -e "  ${GREEN}8)${NC} View Logs"
    echo -e "  ${GREEN}H)${NC} Help & Documentation"
    echo -e "  ${RED}0)${NC} Exit"
    echo ""
    echo -ne "${BOLD}Select an option [0-8/H]:${NC} "
}

###############################################################################
# Cleanup Handler
###############################################################################

cleanup() {
    echo ""
    print_section "Shutting Down"

    # Kill backend
    if [ -n "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID 2>/dev/null || true
        wait $BACKEND_PID 2>/dev/null || true
        print_success "Backend server stopped"
    fi

    # Kill frontend
    if [ -n "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
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

    if ! command -v python3 &> /dev/null; then
        if ! command -v python &> /dev/null; then
            print_error "Python 3 is not installed"
            echo "Please install Python 3.8 or higher"
            return 1
        fi
    fi

    local PYTHON_CMD
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    local PYTHON_VERSION
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION detected"

    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        print_error "pip is not installed"
        return 1
    fi

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

    # Check for requirements.txt - first in backend, then in root
    if [ -f "$BACKEND_REQUIREMENTS" ]; then
        print_success "requirements.txt found in $BACKEND_DIR"
    elif [ -f "$REQUIREMENTS_FILE" ]; then
        print_success "requirements.txt found in project root"
    else
        print_error "requirements.txt not found in $BACKEND_DIR or project root"
        all_ok=false
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

clean_python_cache() {
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

    local PYTHON_CMD
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    local PIP_CMD
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    else
        PIP_CMD="pip"
    fi

    # Determine which requirements file to use
    local req_file=""
    if [ -f "$BACKEND_REQUIREMENTS" ]; then
        req_file="$BACKEND_REQUIREMENTS"
        print_info "Using backend requirements: $BACKEND_REQUIREMENTS"
    elif [ -f "$REQUIREMENTS_FILE" ]; then
        req_file="$REQUIREMENTS_FILE"
        print_info "Using root requirements: $REQUIREMENTS_FILE"
    else
        print_error "No requirements.txt file found"
        return 1
    fi

    print_info "Installing dependencies from $req_file..."
    if $PIP_CMD install -r "$req_file" 2>&1 | tee "$LOG_DIR/pip-install.log"; then
        DEPS_CHECKED=true
        print_success "All dependencies installed successfully"
        return 0
    else
        print_error "Dependency installation failed"
        echo "Check $LOG_DIR/pip-install.log for details"
        return 1
    fi
}

###############################################################################
# Test Functions
###############################################################################

run_tests() {
    print_section "Running Test Suite"

    # Clean cache before running tests
    clean_python_cache

    local PYTHON_CMD
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    print_info "Running test suite with coverage..."
    echo ""

    # Use the TEST_DIR if it exists, otherwise use tests/
    local test_path
    if [ -d "$TEST_DIR" ]; then
        test_path="$TEST_DIR"
    elif [ -d "tests" ]; then
        test_path="tests"
    else
        print_warning "No test directory found, skipping tests"
        return 0
    fi

    $PYTHON_CMD -m pytest "$test_path" \
        --cov=shared \
        --cov="$BACKEND_DIR" \
        --cov-report=term-missing \
        --cov-report=html \
        -v \
        --tb=short \
        2>&1 | tee "$LOG_DIR/test-reports/test-suite.log"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_success "All tests passed!"
        print_info "Coverage report: htmlcov/index.html"
        TESTS_PASSED=true
        return 0
    else
        print_warning "Some tests failed"
        echo ""
        print_info "Coverage report: htmlcov/index.html"
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
# Database Migrations
###############################################################################

run_migrations() {
    print_section "Database Migrations"

    print_info "Running database migrations with Alembic..."

    # Export USE_SQLITE for development/testing
    export USE_SQLITE=true

    # Check if alembic is installed
    if ! command -v alembic &> /dev/null; then
        print_warning "Alembic not found, installing..."
        pip3 install -q alembic
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
    local skip_checks=$1

    local PYTHON_CMD
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    if [ "$skip_checks" != "true" ]; then
        check_python || return 1
        check_directories || return 1
        check_ports || return 1

        if [ "$DEPS_CHECKED" != true ]; then
            echo ""
            echo -ne "Install dependencies now? [Y/n]: "
            read -r deps_choice
            if [[ ! "$deps_choice" =~ ^[Nn]$ ]]; then
                install_dependencies || {
                    print_warning "Dependency installation failed, but continuing..."
                }
            fi
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

    if ! kill -0 $BACKEND_PID 2>/dev/null; then
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

    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend failed to start"
        echo "Check $LOG_DIR/frontend.log for details"
        kill $BACKEND_PID 2>/dev/null || true
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
    echo -e "${GREEN}${BOLD}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║                                                                    ║${NC}"
    echo -e "${GREEN}${BOLD}║        Receipt Extractor is now running!                           ║${NC}"
    echo -e "${GREEN}${BOLD}║                                                                    ║${NC}"
    echo -e "${GREEN}${BOLD}╚════════════════════════════════════════════════════════════════════╝${NC}"
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
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            print_error "Backend process died unexpectedly!"
            echo "Last 20 lines of backend.log:"
            tail -20 "$LOG_DIR/backend.log"
            break
        fi

        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend process died unexpectedly!"
            echo "Last 20 lines of frontend.log:"
            tail -20 "$LOG_DIR/frontend.log"
            break
        fi

        sleep 3
    done
}

###############################################################################
# Launch Modes
###############################################################################

quick_launch() {
    print_banner
    print_section "Quick Launch Mode"
    print_warning "Skipping tests and validation for faster startup"
    echo ""
    start_servers "false"
}

full_launch() {
    print_banner
    print_section "Full Launch Mode"
    print_info "Running comprehensive checks and tests..."
    echo ""

    check_python || return 1
    check_directories || return 1

    echo ""
    echo -ne "Install/check dependencies? [Y/n]: "
    read -r deps_choice
    if [[ ! "$deps_choice" =~ ^[Nn]$ ]]; then
        install_dependencies
    fi

    echo ""
    echo -ne "Run test suite? [Y/n]: "
    read -r test_choice
    if [[ ! "$test_choice" =~ ^[Nn]$ ]]; then
        run_tests || {
            print_error "Tests failed - aborting launch"
            echo -ne "Press Enter to return to menu..."
            read -r
            return 1
        }
    fi

    echo ""
    check_ports || return 1

    echo ""
    echo -ne "Ready to launch. Press Enter to continue..."
    read -r

    start_servers "true"
}

###############################################################################
# System Health Report
###############################################################################

system_health_report() {
    print_section "System Health Report"

    local PYTHON_CMD
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    echo ""
    echo -e "${BOLD}Environment:${NC}"
    echo "  Python: $($PYTHON_CMD --version 2>&1)"
    echo "  Project Root: $PROJECT_ROOT"
    echo "  Log Directory: $LOG_DIR"
    echo ""

    echo -e "${BOLD}Directory Structure:${NC}"
    [ -d "$BACKEND_DIR" ] && echo -e "  Backend:  ${GREEN}[EXISTS]${NC} ($BACKEND_DIR)" || echo -e "  Backend:  ${RED}[MISSING]${NC}"
    [ -d "$FRONTEND_DIR" ] && echo -e "  Frontend: ${GREEN}[EXISTS]${NC} ($FRONTEND_DIR)" || echo -e "  Frontend: ${RED}[MISSING]${NC}"
    [ -f "$BACKEND_REQUIREMENTS" ] || [ -f "$REQUIREMENTS_FILE" ] && echo -e "  Requirements: ${GREEN}[FOUND]${NC}" || echo -e "  Requirements: ${RED}[MISSING]${NC}"
    echo ""

    echo -e "${BOLD}Services:${NC}"
    echo "  Backend Port: $BACKEND_PORT"
    echo "  Frontend Port: $FRONTEND_PORT"

    if [ -n "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "  Backend Status: ${GREEN}[RUNNING]${NC} (PID: $BACKEND_PID)"
    else
        echo -e "  Backend Status: ${YELLOW}[NOT RUNNING]${NC}"
    fi

    if [ -n "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "  Frontend Status: ${GREEN}[RUNNING]${NC} (PID: $FRONTEND_PID)"
    else
        echo -e "  Frontend Status: ${YELLOW}[NOT RUNNING]${NC}"
    fi

    echo ""
    echo -e "${BOLD}Tests & Dependencies:${NC}"
    [ "$DEPS_CHECKED" = true ] && echo -e "  Dependencies: ${GREEN}[VERIFIED]${NC}" || echo -e "  Dependencies: ${YELLOW}[NOT CHECKED]${NC}"
    [ "$TESTS_PASSED" = true ] && echo -e "  Tests: ${GREEN}[PASSED]${NC}" || echo -e "  Tests: ${YELLOW}[NOT RUN]${NC}"

    echo ""
    echo -ne "Press Enter to continue..."
    read -r
}

###############################################################################
# View Logs
###############################################################################

view_logs() {
    print_section "Log Viewer"

    echo ""
    echo "Available logs:"
    echo "  1) Backend log"
    echo "  2) Frontend log"
    echo "  3) Test reports"
    echo "  4) Dependency install log"
    echo "  5) Back to main menu"
    echo ""
    echo -ne "Select log to view [1-5]: "
    read -r log_choice

    case $log_choice in
        1)
            if [ -f "$LOG_DIR/backend.log" ]; then
                less "$LOG_DIR/backend.log"
            else
                print_warning "Backend log not found"
                sleep 2
            fi
            ;;
        2)
            if [ -f "$LOG_DIR/frontend.log" ]; then
                less "$LOG_DIR/frontend.log"
            else
                print_warning "Frontend log not found"
                sleep 2
            fi
            ;;
        3)
            if [ -d "$LOG_DIR/test-reports" ] && [ "$(ls -A $LOG_DIR/test-reports 2>/dev/null)" ]; then
                ls -1 "$LOG_DIR/test-reports"
                echo ""
                echo -ne "Enter log filename to view: "
                read -r test_log
                if [ -f "$LOG_DIR/test-reports/$test_log" ]; then
                    less "$LOG_DIR/test-reports/$test_log"
                fi
            else
                print_warning "No test reports found"
                sleep 2
            fi
            ;;
        4)
            if [ -f "$LOG_DIR/pip-install.log" ]; then
                less "$LOG_DIR/pip-install.log"
            else
                print_warning "Dependency log not found"
                sleep 2
            fi
            ;;
    esac
}

###############################################################################
# Help
###############################################################################

show_help() {
    print_section "Help & Documentation"

    echo ""
    echo -e "${BOLD}Quick Start:${NC}"
    echo "  1. Select option 2 (Full Launch) for first-time setup"
    echo "  2. This will check dependencies, run tests, and start the app"
    echo "  3. Your browser will open automatically to the app"
    echo ""
    echo -e "${BOLD}Command Line Options:${NC}"
    echo "  ./launch.sh          Interactive menu (default)"
    echo "  ./launch.sh --quick  Quick launch (skip tests)"
    echo "  ./launch.sh --test   Run tests only"
    echo "  ./launch.sh --clean  Clean cache only"
    echo "  ./launch.sh --help   Show this help"
    echo ""
    echo -e "${BOLD}Menu Options:${NC}"
    echo "  ${GREEN}Quick Launch:${NC} Start app immediately without tests"
    echo "  ${GREEN}Full Launch:${NC} Run all checks and tests before starting"
    echo "  ${GREEN}Run Tests:${NC} Execute test suite without starting app"
    echo "  ${GREEN}Check Dependencies:${NC} Verify and install required packages"
    echo "  ${GREEN}Health Report:${NC} View system status and diagnostics"
    echo "  ${GREEN}Clean Cache:${NC} Remove Python bytecode and test cache"
    echo "  ${GREEN}Migrations:${NC} Run database migrations"
    echo "  ${GREEN}View Logs:${NC} Browse application logs"
    echo ""
    echo -e "${BOLD}Logs Location:${NC}"
    echo "  All logs are stored in: $PROJECT_ROOT/$LOG_DIR/"
    echo ""
    echo -e "${BOLD}Features Fixed in v4.0:${NC}"
    echo "  - Fixed all path resolution issues"
    echo "  - Works from any directory location"
    echo "  - Unified all three scripts into one"
    echo "  - Proper requirements.txt detection"
    echo "  - Improved error handling and logging"
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
        test|tests|--test)
            print_banner
            run_tests
            exit $?
            ;;
        quick|--quick)
            quick_launch
            exit $?
            ;;
        dev|start|serve|--dev)
            print_banner
            install_dependencies
            start_servers "false"
            exit $?
            ;;
        clean|--clean)
            print_banner
            clean_python_cache
            echo ""
            print_success "Cleanup complete"
            exit 0
            ;;
        deps|dependencies|--deps)
            print_banner
            install_dependencies
            exit $?
            ;;
        migrate|migrations|--migrate)
            print_banner
            run_migrations
            exit $?
            ;;
        health|--health)
            print_banner
            system_health_report
            exit $?
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
                        quick_launch
                        ;;
                    2)
                        full_launch
                        ;;
                    3)
                        print_banner
                        run_tests
                        echo ""
                        echo -ne "Press Enter to continue..."
                        read -r
                        ;;
                    4)
                        print_banner
                        install_dependencies
                        echo ""
                        echo -ne "Press Enter to continue..."
                        read -r
                        ;;
                    5)
                        print_banner
                        system_health_report
                        ;;
                    6)
                        print_banner
                        clean_python_cache
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
                        view_logs
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
