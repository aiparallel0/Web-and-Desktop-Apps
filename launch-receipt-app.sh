#!/bin/bash

###############################################################################
# Receipt Extractor - Sophisticated Launcher with Professional UI
#
# Features:
# - Interactive menu-driven interface
# - Automated testing and validation
# - Dependency checks and installation
# - GPU detection and configuration
# - Health monitoring and diagnostics
# - Professional error handling
# - Detailed logging and reporting
###############################################################################

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

# Unicode symbols (fallback to ASCII if not supported)
CHECK_MARK="[OK]"
CROSS_MARK="[FAIL]"
WARNING_MARK="[WARN]"
INFO_MARK="[INFO]"
ROCKET="[LAUNCH]"
WRENCH="[TOOL]"
TEST_TUBE="[TEST]"

# Configuration
BACKEND_PORT=5000
FRONTEND_PORT=3000
BACKEND_DIR="web-app/backend"
FRONTEND_DIR="web-app/frontend"
LOG_DIR="logs"
TEST_DIR="tests"

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
HEALTH_STATUS="unknown"

###############################################################################
# UI Functions
###############################################################################

print_banner() {
    clear
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║        Receipt Extractor - Professional Launcher v2.0          ║"
    echo "║                                                                ║"
    echo "║    AI-Powered Receipt Processing with Advanced OCR Models      ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_separator() {
    echo -e "${DIM}────────────────────────────────────────────────────────────────${NC}"
}

print_section() {
    echo ""
    echo -e "${BOLD}${BLUE}▶ $1${NC}"
    print_separator
}

print_success() {
    echo -e "${GREEN}${CHECK_MARK}${NC} $1"
}

print_error() {
    echo -e "${RED}${CROSS_MARK}${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}${WARNING_MARK}${NC} $1"
}

print_info() {
    echo -e "${CYAN}${INFO_MARK}${NC} $1"
}

show_menu() {
    print_banner
    echo -e "${BOLD}Main Menu:${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} ${ROCKET} Quick Launch (Skip Tests)"
    echo -e "  ${GREEN}2)${NC} ${ROCKET} Full Launch (With Tests & Validation)"
    echo -e "  ${GREEN}3)${NC} ${TEST_TUBE} Run Tests Only"
    echo -e "  ${GREEN}4)${NC} ${WRENCH} Check & Install Dependencies"
    echo -e "  ${GREEN}5)${NC} ${WRENCH} Check GPU Status"
    echo -e "  ${GREEN}6)${NC} ${INFO_MARK} System Health Report"
    echo -e "  ${GREEN}7)${NC} ${INFO_MARK} View Logs"
    echo -e "  ${GREEN}8)${NC} ${WRENCH} Developer Mode (Debug Logging)"
    echo -e "  ${GREEN}9)${NC} ${INFO_MARK} Help & Documentation"
    echo -e "  ${CYAN}E)${NC} ${INFO_MARK} Export System Report for AI Analysis"
    echo -e "  ${RED}0)${NC} Exit"
    echo ""
    echo -ne "${BOLD}Select an option [0-9/E]:${NC} "
}

###############################################################################
# Cleanup and Signal Handling
###############################################################################

cleanup() {
    echo ""
    print_section "Shutting Down"

    # Kill backend
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        wait $BACKEND_PID 2>/dev/null
        print_success "Backend server stopped"
    fi

    # Kill frontend
    if [ ! -z "$FRONTEND_PID" ]; then
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
        print_error "Python 3 is not installed"
        echo "Please install Python 3.8 or higher"
        return 1
    fi

    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION detected"

    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        return 1
    fi

    print_success "pip3 available"
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

    if [ -f "check_dependencies.py" ]; then
        print_info "Running dependency checker with auto-install..."
        echo ""
        python3 check_dependencies.py --auto-install
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

    if [ -f "check_gpu.py" ]; then
        python3 check_gpu.py 2>&1 | tee "$LOG_DIR/gpu-check.log"

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
    read
}

run_tests() {
    print_section "Running Test Suite"

    local test_failed=false
    local test_count=0
    local passed_count=0

    # Run system health test
    if [ -f "tests/test_system_health.py" ]; then
        echo ""
        print_info "Running system health tests..."
        python3 -m pytest tests/test_system_health.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/health.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "System health tests passed"
            ((passed_count++))
        else
            print_error "System health tests failed"
            test_failed=true
        fi
        ((test_count++))
    fi

    # Run image processing tests
    if [ -f "tests/shared/test_image_processing.py" ]; then
        echo ""
        print_info "Running image processing tests..."
        python3 -m pytest tests/shared/test_image_processing.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/image.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Image processing tests passed"
            ((passed_count++))
        else
            print_error "Image processing tests failed"
            test_failed=true
        fi
        ((test_count++))
    fi

    # Run model manager tests
    if [ -f "tests/shared/test_model_manager.py" ]; then
        echo ""
        print_info "Running model manager tests..."
        python3 -m pytest tests/shared/test_model_manager.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/models.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Model manager tests passed"
            ((passed_count++))
        else
            print_warning "Model manager tests failed (may require AI models)"
            test_failed=true
        fi
        ((test_count++))
    fi

    # Run base processor tests (NEW - comprehensive coverage)
    if [ -f "tests/shared/test_base_processor.py" ]; then
        echo ""
        print_info "Running base processor tests..."
        python3 -m pytest tests/shared/test_base_processor.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/base_processor.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Base processor tests passed"
            ((passed_count++))
        else
            print_warning "Base processor tests failed"
            test_failed=true
        fi
        ((test_count++))
    fi

    # Run EasyOCR processor tests (NEW - requires mocking)
    if [ -f "tests/shared/test_easyocr_processor.py" ]; then
        echo ""
        print_info "Running EasyOCR processor tests..."
        python3 -m pytest tests/shared/test_easyocr_processor.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/easyocr_processor.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "EasyOCR processor tests passed"
            ((passed_count++))
        else
            print_warning "EasyOCR processor tests failed (may require dependencies)"
            test_failed=true
        fi
        ((test_count++))
    fi

    # Run Paddle processor tests (NEW - requires mocking)
    if [ -f "tests/shared/test_paddle_processor.py" ]; then
        echo ""
        print_info "Running Paddle processor tests..."
        python3 -m pytest tests/shared/test_paddle_processor.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/paddle_processor.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Paddle processor tests passed"
            ((passed_count++))
        else
            print_warning "Paddle processor tests failed (may require dependencies)"
            test_failed=true
        fi
        ((test_count++))
    fi

    # Run Donut processor tests (NEW - requires mocking)
    if [ -f "tests/shared/test_donut_processor.py" ]; then
        echo ""
        print_info "Running Donut processor tests..."
        python3 -m pytest tests/shared/test_donut_processor.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/donut_processor.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Donut processor tests passed"
            ((passed_count++))
        else
            print_warning "Donut processor tests failed (may require dependencies)"
            test_failed=true
        fi
        ((test_count++))
    fi

    # Run API tests
    if [ -f "tests/web/test_api.py" ]; then
        echo ""
        print_info "Running API tests..."
        python3 -m pytest tests/web/test_api.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/api.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "API tests passed"
            ((passed_count++))
        else
            print_error "API tests failed"
            test_failed=true
        fi
        ((test_count++))
    fi

    # Run simple OCR test
    if [ -f "test_ocr_simple.py" ]; then
        echo ""
        print_info "Running OCR validation test..."
        python3 test_ocr_simple.py 2>&1 | tee "$LOG_DIR/test-reports/ocr.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "OCR validation passed"
            ((passed_count++))
        else
            print_warning "OCR validation failed (may need Tesseract)"
        fi
        ((test_count++))
    fi

    # Run backend authentication tests (NEW - comprehensive security coverage)
    if [ -f "tests/backend/auth/test_jwt_handler.py" ]; then
        echo ""
        print_info "Running JWT authentication tests..."
        python3 -m pytest tests/backend/auth/test_jwt_handler.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/jwt_auth.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "JWT authentication tests passed"
            ((passed_count++))
        else
            print_warning "JWT authentication tests failed"
            test_failed=true
        fi
        ((test_count++))
    fi

    if [ -f "tests/backend/auth/test_password.py" ]; then
        echo ""
        print_info "Running password security tests..."
        python3 -m pytest tests/backend/auth/test_password.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/password_security.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Password security tests passed"
            ((passed_count++))
        else
            print_warning "Password security tests failed"
            test_failed=true
        fi
        ((test_count++))
    fi

    if [ -f "tests/backend/auth/test_decorators.py" ]; then
        echo ""
        print_info "Running auth decorator tests..."
        python3 -m pytest tests/backend/auth/test_decorators.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/auth_decorators.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Auth decorator tests passed"
            ((passed_count++))
        else
            print_warning "Auth decorator tests failed"
            test_failed=true
        fi
        ((test_count++))
    fi

    # Run database tests (NEW - data integrity coverage)
    if [ -f "tests/backend/database/test_models.py" ]; then
        echo ""
        print_info "Running database model tests..."
        python3 -m pytest tests/backend/database/test_models.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/db_models.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Database model tests passed"
            ((passed_count++))
        else
            print_warning "Database model tests failed"
            test_failed=true
        fi
        ((test_count++))
    fi

    if [ -f "tests/backend/database/test_connection.py" ]; then
        echo ""
        print_info "Running database connection tests..."
        python3 -m pytest tests/backend/database/test_connection.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/db_connection.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Database connection tests passed"
            ((passed_count++))
        else
            print_warning "Database connection tests failed"
            test_failed=true
        fi
        ((test_count++))
    fi

    # Run validation tests (NEW - input security coverage)
    if [ -f "tests/backend/validation/test_schemas.py" ]; then
        echo ""
        print_info "Running input validation tests..."
        python3 -m pytest tests/backend/validation/test_schemas.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/validation_schemas.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Input validation tests passed"
            ((passed_count++))
        else
            print_warning "Input validation tests failed"
            test_failed=true
        fi
        ((test_count++))
    fi

    # Run Flask app tests (NEW - endpoint coverage)
    if [ -f "tests/backend/test_app.py" ]; then
        echo ""
        print_info "Running Flask application tests..."
        python3 -m pytest tests/backend/test_app.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/flask_app.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Flask application tests passed"
            ((passed_count++))
        else
            print_warning "Flask application tests failed"
            test_failed=true
        fi
        ((test_count++))
    fi

    # Run ML model tests (NEW - finetuning coverage)
    if [ -f "tests/shared/models/test_donut_finetuner.py" ]; then
        echo ""
        print_info "Running Donut finetuner tests..."
        python3 -m pytest tests/shared/models/test_donut_finetuner.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/donut_finetuner.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Donut finetuner tests passed"
            ((passed_count++))
        else
            print_warning "Donut finetuner tests failed (may require dependencies)"
            test_failed=true
        fi
        ((test_count++))
    fi

    # Run logger tests (NEW - utility coverage)
    if [ -f "tests/shared/utils/test_logger.py" ]; then
        echo ""
        print_info "Running logger utility tests..."
        python3 -m pytest tests/shared/utils/test_logger.py -v --tb=short 2>&1 | tee "$LOG_DIR/test-reports/logger_utils.log"
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Logger utility tests passed"
            ((passed_count++))
        else
            print_warning "Logger utility tests failed"
            test_failed=true
        fi
        ((test_count++))
    fi

    echo ""
    print_separator
    echo -e "${BOLD}Test Summary:${NC}"
    echo -e "  Total Tests: ${test_count}"
    echo -e "  Passed: ${GREEN}${passed_count}${NC}"
    echo -e "  Failed: ${RED}$((test_count - passed_count))${NC}"

    if [ $test_failed = true ]; then
        echo ""
        print_warning "Some tests failed, but app may still work"
        echo -ne "Continue anyway? [y/N]: "
        read continue_choice
        if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi

    TESTS_PASSED=true
    return 0
}

system_health_report() {
    print_section "System Health Report"

    echo ""
    echo -e "${BOLD}Environment:${NC}"
    echo "  Python: $(python3 --version 2>&1)"
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
    if [ ! -z "$BACKEND_PID" ]; then
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo -e "  Backend: ${GREEN}Running${NC} (PID: $BACKEND_PID)"
        else
            echo -e "  Backend: ${RED}Stopped${NC}"
        fi
    else
        echo -e "  Backend: ${YELLOW}Not Started${NC}"
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
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
    read
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
    read log_choice

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
                read test_log
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
    echo -e "${BOLD}Menu Options:${NC}"
    echo "  ${GREEN}Quick Launch:${NC} Start app immediately without tests"
    echo "  ${GREEN}Full Launch:${NC} Run all checks and tests before starting"
    echo "  ${GREEN}Run Tests:${NC} Execute test suite without starting app"
    echo "  ${GREEN}Check Dependencies:${NC} Verify and install required packages"
    echo "  ${GREEN}Check GPU:${NC} Detect GPU availability for acceleration"
    echo "  ${GREEN}Health Report:${NC} View system status and diagnostics"
    echo ""
    echo -e "${BOLD}Documentation:${NC}"
    echo "  - README.md: Main documentation"
    echo "  - SETUP.md: Installation guide"
    echo "  - WINDOWS_INSTALLATION.md: Windows-specific setup"
    echo "  - web-app/README.md: Web app documentation"
    echo ""
    echo -e "${BOLD}Logs Location:${NC}"
    echo "  All logs are stored in: $LOG_DIR/"
    echo ""
    echo -ne "Press Enter to continue..."
    read
}

###############################################################################
# Launch Functions
###############################################################################

start_servers() {
    local skip_checks=$1

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
    python3 app.py > "$SCRIPT_DIR/$LOG_DIR/backend.log" 2>&1 &
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
    python3 -m http.server $FRONTEND_PORT > "$SCRIPT_DIR/$LOG_DIR/frontend.log" 2>&1 &
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
    echo -e "${GREEN}${BOLD}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║                                                                ║${NC}"
    echo -e "${GREEN}${BOLD}║        Receipt Extractor is now running!                      ║${NC}"
    echo -e "${GREEN}${BOLD}║                                                                ║${NC}"
    echo -e "${GREEN}${BOLD}╚════════════════════════════════════════════════════════════════╝${NC}"
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
    read gpu_choice
    if [[ "$gpu_choice" =~ ^[Yy]$ ]]; then
        check_gpu_status
    fi

    echo ""
    echo -ne "Run test suite? [Y/n]: "
    read test_choice
    if [[ ! "$test_choice" =~ ^[Nn]$ ]]; then
        run_tests || {
            print_error "Tests failed - aborting launch"
            echo -ne "Press Enter to return to menu..."
            read
            return 1
        }
    fi

    echo ""
    check_ports || return 1

    echo ""
    echo -ne "Ready to launch. Press Enter to continue..."
    read

    start_servers "true"
}

export_system_report() {
    print_section "Exporting System Report for AI Analysis"

    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local report_file="$LOG_DIR/ai-analysis-report_${timestamp}.md"

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
        echo "- **Python Version:** $(python3 --version 2>&1)"
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

        echo "## Dependency Status"
        echo ""
        if [ -f "$LOG_DIR/pip-install.log" ]; then
            echo "### Last Dependency Install Log"
            echo "\`\`\`"
            tail -50 "$LOG_DIR/pip-install.log" 2>/dev/null
            echo "\`\`\`"
            echo ""
        fi

        echo "### Python Packages"
        echo "\`\`\`"
        python3 -m pip list 2>&1 | grep -E "(flask|torch|transformers|paddleocr|easyocr|opencv|pillow)" || echo "Package list unavailable"
        echo "\`\`\`"
        echo ""

        echo "## GPU Configuration"
        echo ""
        if [ -f "$LOG_DIR/gpu-check.log" ]; then
            echo "### GPU Detection Results"
            echo "\`\`\`"
            cat "$LOG_DIR/gpu-check.log" 2>/dev/null
            echo "\`\`\`"
        else
            echo "GPU check not run. Status: ${GPU_AVAILABLE}"
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

        if [ -d "$LOG_DIR/test-reports" ] && [ "$(ls -A $LOG_DIR/test-reports 2>/dev/null)" ]; then
            for test_log in "$LOG_DIR/test-reports"/*.log; do
                if [ -f "$test_log" ]; then
                    echo "### Test: $(basename "$test_log" .log)"
                    echo "\`\`\`"
                    cat "$test_log"
                    echo "\`\`\`"
                    echo ""
                fi
            done
        else
            echo "No test results available. Run option 3 to execute tests."
        fi

        echo "## Application Logs"
        echo ""

        if [ -f "$LOG_DIR/backend.log" ]; then
            echo "### Backend Log (Last 100 lines)"
            echo "\`\`\`"
            tail -100 "$LOG_DIR/backend.log" 2>/dev/null
            echo "\`\`\`"
            echo ""
        else
            echo "Backend log not available (app not started)"
            echo ""
        fi

        if [ -f "$LOG_DIR/frontend.log" ]; then
            echo "### Frontend Log (Last 50 lines)"
            echo "\`\`\`"
            tail -50 "$LOG_DIR/frontend.log" 2>/dev/null
            echo "\`\`\`"
            echo ""
        else
            echo "Frontend log not available (app not started)"
            echo ""
        fi

        echo "## Configuration Files"
        echo ""

        if [ -f "shared/config/models_config.json" ]; then
            echo "### Models Configuration"
            echo "\`\`\`json"
            cat "shared/config/models_config.json" 2>/dev/null
            echo "\`\`\`"
            echo ""
        fi

        echo "## File Structure"
        echo ""
        echo "\`\`\`"
        tree -L 3 -I '__pycache__|*.pyc|node_modules' . 2>/dev/null || find . -maxdepth 3 -type f -name "*.py" | head -50
        echo "\`\`\`"
        echo ""

        echo "## Current Issues & Errors"
        echo ""
        echo "### Recent Errors from Logs"
        if [ -f "$LOG_DIR/backend.log" ]; then
            echo "\`\`\`"
            grep -i "error\|exception\|fail" "$LOG_DIR/backend.log" | tail -20 2>/dev/null || echo "No errors found"
            echo "\`\`\`"
        else
            echo "No backend log available"
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

        echo "### Common Development Tasks"
        echo "- **Add new model:** Update \`shared/config/models_config.json\`"
        echo "- **Fix test failures:** Check \`tests/\` directory"
        echo "- **Debug backend:** Review \`logs/backend.log\`"
        echo "- **Update dependencies:** Modify \`web-app/backend/requirements.txt\`"
        echo ""

        echo "### Files to Focus On"
        echo "- \`web-app/backend/app.py\` - Main API server"
        echo "- \`shared/models/model_manager.py\` - Model loading logic"
        echo "- \`shared/models/donut_processor.py\` - Donut model processing"
        echo "- \`shared/models/paddle_processor.py\` - PaddleOCR processing"
        echo "- \`tests/\` - Test suite"
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
    echo -e "${BOLD}Example prompts:${NC}"
    echo '  - "Analyze this system report and identify all errors"'
    echo '  - "Based on this report, fix the failing tests"'
    echo '  - "Review the configuration and suggest optimizations"'
    echo ""
    echo -ne "Open report now? [y/N]: "
    read view_choice
    if [[ "$view_choice" =~ ^[Yy]$ ]]; then
        less "$report_file"
    fi

    echo ""
    echo -ne "Press Enter to continue..."
    read
}

###############################################################################
# Main Program
###############################################################################

main() {
    while true; do
        show_menu
        read choice

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
                read
                ;;
            4)
                print_banner
                run_dependency_check
                echo ""
                echo -ne "Press Enter to continue..."
                read
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
                view_logs
                ;;
            8)
                print_banner
                print_section "Developer Mode"
                print_info "Starting with debug logging enabled..."
                export FLASK_DEBUG=1
                export FLASK_ENV=development
                start_servers "false"
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
    read sudo_choice
    if [[ ! "$sudo_choice" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start main program
main
