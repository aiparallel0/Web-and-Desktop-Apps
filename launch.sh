#!/bin/bash
###############################################################################
# Receipt Extractor - Unified Launcher Script
# 
# This script combines all launcher functionality into one coherent script with:
# - Automatic cache cleaning (Python bytecode, pytest cache)
# - Dependency checking and installation
# - Backend and Frontend server management
# - GPU detection
# - Test execution
# - Health monitoring
# - AI Analysis Report generation
#
# Usage: ./launch.sh [option]
#   No option: Interactive menu
#   --quick: Quick launch (skip tests)
#   --test:  Run tests only
#   --clean: Clean cache only
#
# UI designed for maximum compatibility with ASCII terminals (1970s+)
###############################################################################

set -e

# Colors and formatting (optional - degrades gracefully on non-color terminals)
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=5000
FRONTEND_PORT=3000
BACKEND_DIR="web-app/backend"
FRONTEND_DIR="web-app/frontend"
LOG_DIR="logs"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

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
    echo "+================================================================+"
    echo "|                                                                |"
    echo "|        Receipt Extractor - Unified Launcher v3.0               |"
    echo "|                                                                |"
    echo "|    AI-Powered Receipt Processing with Advanced OCR Models      |"
    echo "|                                                                |"
    echo "+================================================================+"
    echo -e "${NC}"
}

print_separator() {
    echo -e "${DIM}----------------------------------------------------------------${NC}"
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
    echo -e "  ${GREEN}5)${NC} Check GPU Status"
    echo -e "  ${GREEN}6)${NC} System Health Report"
    echo -e "  ${GREEN}7)${NC} Clean Cache (Python bytecode & pytest)"
    echo -e "  ${GREEN}8)${NC} View Logs"
    echo -e "  ${GREEN}9)${NC} Help & Documentation"
    echo -e "  ${CYAN}E)${NC} Export System Report for AI Analysis"
    echo -e "  ${RED}0)${NC} Exit"
    echo ""
    echo -ne "${BOLD}Select an option [0-9/E]:${NC} "
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
    done < <(find . -type d -name "__pycache__" -print0 2>/dev/null)
    
    # Remove .pyc files
    while IFS= read -r -d '' file; do
        rm -f "$file" 2>/dev/null && ((pyc_count++)) || true
    done < <(find . -type f -name "*.pyc" -print0 2>/dev/null)
    
    # Remove pytest cache
    if [ -d ".pytest_cache" ]; then
        rm -rf .pytest_cache
        print_success "Removed .pytest_cache directory"
    fi
    
    # Remove coverage cache
    if [ -f ".coverage" ]; then
        rm -f .coverage
        print_success "Removed .coverage file"
    fi
    
    if [ -d "htmlcov" ]; then
        rm -rf htmlcov
        print_success "Removed htmlcov directory"
    fi
    
    print_success "Removed $pycache_count __pycache__ directories"
    print_success "Removed $pyc_count .pyc files"
    print_info "Cache cleanup complete - tests will use fresh code"
}

###############################################################################
# Cleanup and Signal Handling
###############################################################################

cleanup() {
    echo ""
    print_section "Shutting Down"

    # Kill backend
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        wait $BACKEND_PID 2>/dev/null
        print_success "Backend server stopped"
    fi

    # Kill frontend
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        wait $FRONTEND_PID 2>/dev/null
        print_success "Frontend server stopped"
    fi

    echo ""
    echo -e "${GREEN}${BOLD}Cleanup complete. Thank you for using Receipt Extractor!${NC}"
    exit 0
}

# Set up trap to catch Ctrl+C
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
        print_error "Backend directory not found: $BACKEND_DIR"
        all_ok=false
    else
        print_success "Backend directory exists"
    fi

    if [ ! -d "$FRONTEND_DIR" ]; then
        print_error "Frontend directory not found: $FRONTEND_DIR"
        all_ok=false
    else
        print_success "Frontend directory exists"
    fi

    if [ ! -f "$BACKEND_DIR/requirements.txt" ]; then
        print_error "requirements.txt not found in $BACKEND_DIR"
        all_ok=false
    else
        print_success "requirements.txt found"
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
# Advanced Features
###############################################################################

run_dependency_check() {
    print_section "Dependency Analysis"

    local PYTHON_CMD
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    if [ -f "check_dependencies.py" ]; then
        print_info "Running dependency checker with auto-install..."
        echo ""
        $PYTHON_CMD check_dependencies.py --install
        local exit_code=$?

        if [ $exit_code -eq 0 ]; then
            DEPS_CHECKED=true
            print_success "All dependencies verified"
            return 0
        else
            print_warning "Some dependencies may be missing"
            echo ""
            echo "You can:"
            echo "  1. Run 'python3 check_dependencies.py' interactively for more control"
            echo "  2. Install manually: pip install -r web-app/backend/requirements.txt"
            return 1
        fi
    else
        print_warning "check_dependencies.py not found, using pip install"
        cd "$BACKEND_DIR"
        pip3 install -q -r requirements.txt 2>"$SCRIPT_DIR/$LOG_DIR/pip-install.log"
        cd "$SCRIPT_DIR"
        DEPS_CHECKED=true
        return 0
    fi
}

check_gpu_status() {
    print_section "GPU Detection & Configuration"

    local PYTHON_CMD
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    if [ -f "check_gpu.py" ]; then
        $PYTHON_CMD check_gpu.py 2>&1 | tee "$LOG_DIR/gpu-check.log"

        if grep -q "CUDA available: True" "$LOG_DIR/gpu-check.log" 2>/dev/null; then
            GPU_AVAILABLE=true
            print_success "GPU acceleration available"
        else
            GPU_AVAILABLE=false
            print_warning "No GPU detected - models will run on CPU"
        fi
    else
        print_warning "GPU check utility not found"
        GPU_AVAILABLE=false
    fi

    echo ""
    echo -ne "Press Enter to continue..."
    read -r
}

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

    local test_failed=false
    local test_count=0
    local passed_count=0

    # Run comprehensive test suite via python runner
    if [ -f "run_all_tests.py" ]; then
        print_info "Running comprehensive test suite..."
        $PYTHON_CMD run_all_tests.py 2>&1 | tee "$LOG_DIR/test-reports/full-suite.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Comprehensive test suite passed"
            TESTS_PASSED=true
            return 0
        else
            print_warning "Some tests failed"
            test_failed=true
        fi
    else
        # Fall back to individual test files
        # Run system health test
        if [ -f "tests/test_system_health.py" ]; then
            echo ""
            print_info "Running system health tests..."
            $PYTHON_CMD -m pytest tests/test_system_health.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/health.log"
            if [ ${PIPESTATUS[0]} -eq 0 ]; then
                print_success "System health tests passed"
                ((passed_count++))
            else
                print_error "System health tests failed"
                test_failed=true
            fi
            ((test_count++))
        fi

        # Run API tests
        if [ -f "tests/web/test_api.py" ]; then
            echo ""
            print_info "Running API tests..."
            $PYTHON_CMD -m pytest tests/web/test_api.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/api.log"
            if [ ${PIPESTATUS[0]} -eq 0 ]; then
                print_success "API tests passed"
                ((passed_count++))
            else
                print_error "API tests failed"
                test_failed=true
            fi
            ((test_count++))
        fi
    fi

    echo ""
    print_separator
    echo -e "${BOLD}Test Summary:${NC}"
    echo -e "  Total Suites: ${test_count}"
    echo -e "  Passed: ${GREEN}${passed_count}${NC}"
    echo -e "  Failed: ${RED}$((test_count - passed_count))${NC}"

    if [ $test_failed = true ]; then
        echo ""
        print_warning "Some tests failed, but app may still work"
        echo -ne "Continue anyway? [y/N]: "
        read -r continue_choice
        if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi

    TESTS_PASSED=true
    return 0
}

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
    echo "  Working Directory: $SCRIPT_DIR"
    echo "  Log Directory: $LOG_DIR"

    echo ""
    echo -e "${BOLD}Dependencies:${NC}"
    if [ "$DEPS_CHECKED" = true ]; then
        echo -e "  Status: ${GREEN}Verified${NC}"
    else
        echo -e "  Status: ${YELLOW}Not Checked${NC}"
    fi

    echo ""
    echo -e "${BOLD}GPU Acceleration:${NC}"
    if [ "$GPU_AVAILABLE" = true ]; then
        echo -e "  Status: ${GREEN}Available${NC}"
    else
        echo -e "  Status: ${YELLOW}Not Available (CPU mode)${NC}"
    fi

    echo ""
    echo -e "${BOLD}Tests:${NC}"
    if [ "$TESTS_PASSED" = true ]; then
        echo -e "  Status: ${GREEN}Passed${NC}"
    else
        echo -e "  Status: ${YELLOW}Not Run${NC}"
    fi

    echo ""
    echo -e "${BOLD}Ports:${NC}"
    echo "  Backend: $BACKEND_PORT"
    echo "  Frontend: $FRONTEND_PORT"

    echo ""
    echo -e "${BOLD}Services:${NC}"
    if [ -n "$BACKEND_PID" ]; then
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo -e "  Backend: ${GREEN}Running${NC} (PID: $BACKEND_PID)"
        else
            echo -e "  Backend: ${RED}Stopped${NC}"
        fi
    else
        echo -e "  Backend: ${YELLOW}Not Started${NC}"
    fi

    if [ -n "$FRONTEND_PID" ]; then
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo -e "  Frontend: ${GREEN}Running${NC} (PID: $FRONTEND_PID)"
        else
            echo -e "  Frontend: ${RED}Stopped${NC}"
        fi
    else
        echo -e "  Frontend: ${YELLOW}Not Started${NC}"
    fi

    echo ""
    echo -ne "Press Enter to continue..."
    read -r
}

view_logs() {
    print_section "Log Viewer"

    echo ""
    echo "Available logs:"
    echo "  1) Backend log"
    echo "  2) Frontend log"
    echo "  3) Test reports"
    echo "  4) Dependency check log"
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
            if [ -d "$LOG_DIR/test-reports" ] && [ "$(ls -A $LOG_DIR/test-reports)" ]; then
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
    echo ""
    echo -e "${BOLD}Menu Options:${NC}"
    echo "  ${GREEN}Quick Launch:${NC} Start app immediately without tests"
    echo "  ${GREEN}Full Launch:${NC} Run all checks and tests before starting"
    echo "  ${GREEN}Run Tests:${NC} Execute test suite without starting app"
    echo "  ${GREEN}Check Dependencies:${NC} Verify and install required packages"
    echo "  ${GREEN}Check GPU:${NC} Detect GPU availability for acceleration"
    echo "  ${GREEN}Health Report:${NC} View system status and diagnostics"
    echo "  ${GREEN}Clean Cache:${NC} Remove Python bytecode and test cache"
    echo ""
    echo -e "${BOLD}Logs Location:${NC}"
    echo "  All logs are stored in: $LOG_DIR/"
    echo ""
    echo -ne "Press Enter to continue..."
    read -r
}

###############################################################################
# Launch Functions
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
        # Run all checks
        check_python || return 1
        check_directories || return 1
        check_ports || return 1

        if [ "$DEPS_CHECKED" != true ]; then
            run_dependency_check || {
                print_warning "Dependency check failed, but continuing..."
            }
        fi
    fi

    print_section "Starting Services"

    # Start backend
    print_info "Starting backend API server..."
    cd "$BACKEND_DIR"
    $PYTHON_CMD app.py > "$SCRIPT_DIR/$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    cd "$SCRIPT_DIR"

    sleep 3

    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend failed to start"
        echo "Check logs/backend.log for details"
        tail -20 "$LOG_DIR/backend.log"
        return 1
    fi

    print_success "Backend running on http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)"

    # Start frontend
    print_info "Starting frontend web server..."
    cd "$FRONTEND_DIR"
    $PYTHON_CMD -m http.server $FRONTEND_PORT > "$SCRIPT_DIR/$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    cd "$SCRIPT_DIR"

    sleep 2

    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend failed to start"
        echo "Check logs/frontend.log for details"
        kill $BACKEND_PID 2>/dev/null
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
    echo -e "${GREEN}${BOLD}+================================================================+${NC}"
    echo -e "${GREEN}${BOLD}|                                                                |${NC}"
    echo -e "${GREEN}${BOLD}|        Receipt Extractor is now running!                       |${NC}"
    echo -e "${GREEN}${BOLD}|                                                                |${NC}"
    echo -e "${GREEN}${BOLD}+================================================================+${NC}"
    echo ""
    echo -e "  ${BOLD}Frontend:${NC}  ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "  ${BOLD}Backend:${NC}   ${BLUE}http://localhost:$BACKEND_PORT${NC}"
    echo -e "  ${BOLD}API Docs:${NC}  ${BLUE}http://localhost:$BACKEND_PORT/api/health${NC}"
    echo ""
    echo -e "${YELLOW}${BOLD}Press Ctrl+C to stop all servers${NC}"
    echo ""
    echo -e "${DIM}Logs: logs/backend.log | logs/frontend.log${NC}"
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
    run_dependency_check

    echo ""
    echo -ne "Run GPU check? [y/N]: "
    read -r gpu_choice
    if [[ "$gpu_choice" =~ ^[Yy]$ ]]; then
        check_gpu_status
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

export_system_report() {
    print_section "Exporting System Report for AI Analysis"

    local PYTHON_CMD
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local report_file="ai-analysis-report_${timestamp}.md"

    print_info "Generating comprehensive system report..."
    print_info "Format: Markdown (optimized for Claude Code/AI agents)"

    # Generate report
    {
        echo "# Receipt Extractor - System Analysis Report"
        echo "**Generated:** $(date '+%Y-%m-%d %H:%M:%S')"
        echo "**Purpose:** Comprehensive system state for AI-assisted development"
        echo ""
        echo "---"
        echo ""

        echo "## Executive Summary"
        echo ""
        echo "This report contains complete system diagnostics, test results, error logs,"
        echo "and configuration details for the Receipt Extractor application."
        echo "Use this report to understand the current state and identify issues."
        echo ""

        echo "## System Environment"
        echo ""
        echo "### Platform Information"
        echo "- **OS:** $(uname -s)"
        echo "- **Kernel:** $(uname -r)"
        echo "- **Architecture:** $(uname -m)"
        echo "- **Python Version:** $($PYTHON_CMD --version 2>&1)"
        echo "- **Working Directory:** $SCRIPT_DIR"
        echo ""

        echo "### Hardware Resources"
        if command -v free &> /dev/null; then
            echo "- **Memory:** $(free -h | awk '/^Mem:/ {print $2 " total, " $3 " used, " $4 " available"}')"
        fi
        if command -v df &> /dev/null; then
            echo "- **Disk Space:** $(df -h . | awk 'NR==2 {print $2 " total, " $3 " used, " $4 " available"}')"
        fi
        echo ""

        echo "## Test Results"
        echo ""
        if [ "$TESTS_PASSED" = true ]; then
            echo "**Overall Status:** [PASSED]"
        else
            echo "**Overall Status:** [NOT RUN OR FAILED]"
        fi
        echo ""

        echo "## Recommendations for AI Agent"
        echo ""
        echo "### Priority Actions"
        echo "1. Review test results and fix any failing tests"
        echo "2. Check error logs for runtime issues"
        echo "3. Verify all dependencies are installed correctly"
        echo "4. Ensure GPU is configured if AI models are needed"
        echo "5. Review configuration files for correct settings"
        echo ""

        echo "---"
        echo ""
        echo "**End of Report**"
        echo ""
        echo "This report was generated automatically by the Receipt Extractor launcher."
        echo "Use it with AI coding assistants like Claude Code for efficient debugging and development."

    } > "$report_file"

    print_success "Report generated: $report_file"
    echo ""
    echo -e "${BOLD}Report Details:${NC}"
    echo "  - Format: Markdown (.md)"
    echo "  - Size: $(du -h "$report_file" | cut -f1)"
    echo "  - Lines: $(wc -l < "$report_file")"
    echo ""
    echo -e "${BOLD}How to Use:${NC}"
    echo "  1. Share this report with Claude Code or AI assistant"
    echo "  2. Ask it to analyze issues and suggest fixes"
    echo "  3. Request specific improvements or debugging help"
    echo ""
    echo -ne "Open report now? [y/N]: "
    read -r view_choice
    if [[ "$view_choice" =~ ^[Yy]$ ]]; then
        less "$report_file"
    fi

    echo ""
    echo -ne "Press Enter to continue..."
    read -r
}

###############################################################################
# Main Program
###############################################################################

main() {
    # Handle command line arguments
    case "${1:-}" in
        --quick)
            quick_launch
            exit $?
            ;;
        --test)
            print_banner
            run_tests
            exit $?
            ;;
        --clean)
            print_banner
            clean_python_cache
            echo ""
            echo -ne "Press Enter to continue..."
            read -r
            exit 0
            ;;
        --help|-h)
            print_banner
            show_help
            exit 0
            ;;
    esac

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
                run_dependency_check
                echo ""
                echo -ne "Press Enter to continue..."
                read -r
                ;;
            5)
                print_banner
                check_gpu_status
                ;;
            6)
                print_banner
                system_health_report
                ;;
            7)
                print_banner
                clean_python_cache
                echo ""
                echo -ne "Press Enter to continue..."
                read -r
                ;;
            8)
                view_logs
                ;;
            9)
                print_banner
                show_help
                ;;
            [Ee])
                print_banner
                export_system_report
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
}

# Check if running with sudo (warn if so)
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root is not recommended"
    echo -ne "Continue anyway? [y/N]: "
    read -r sudo_choice
    if [[ ! "$sudo_choice" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start main program
main "$@"
