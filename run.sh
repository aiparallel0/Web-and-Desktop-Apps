#!/bin/bash
###############################################################################
# Receipt Extractor - Quick Test & Development Script
#
# A streamlined launcher for testing and development work.
# For full features, use: ./tools/launch.sh
#
# Usage:
#   ./run.sh              # Interactive menu
#   ./run.sh test         # Run tests
#   ./run.sh dev          # Start dev servers
#   ./run.sh quick        # Quick test without coverage
#   ./run.sh clean        # Clean cache and temp files
###############################################################################

set -e

# Set TERM if not set (for compatibility)
export TERM=${TERM:-xterm}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
BACKEND_DIR="web/backend"
FRONTEND_DIR="web/frontend"
TEST_DIR="tools/tests"
BACKEND_PORT=5000
FRONTEND_PORT=3000

# Process IDs
BACKEND_PID=""
FRONTEND_PID=""

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    clear
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║         Receipt Extractor - Development Tool              ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BOLD}━━━ $1 ━━━${NC}"
}

###############################################################################
# Cleanup Handler
###############################################################################

cleanup() {
    echo ""
    print_section "Shutting Down"

    if [ -n "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID 2>/dev/null || true
        print_success "Backend stopped"
    fi

    if [ -n "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_success "Frontend stopped"
    fi

    echo ""
    echo -e "${GREEN}Done!${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

###############################################################################
# Core Functions
###############################################################################

check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo "Please install Python 3.8 or higher"
        return 1
    fi

    local version=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python $version"
    return 0
}

check_dependencies() {
    print_section "Checking Dependencies"

    check_python || return 1

    # Check if required packages are installed
    if ! python3 -c "import flask" 2>/dev/null; then
        print_warning "Flask not found"
        echo ""
        echo -ne "Install dependencies now? [Y/n]: "
        read -r choice
        if [[ ! "$choice" =~ ^[Nn]$ ]]; then
            pip install -r requirements.txt
            print_success "Dependencies installed"
        else
            return 1
        fi
    else
        print_success "Core dependencies found"
    fi

    return 0
}

clean_cache() {
    print_section "Cleaning Cache"

    local count=0

    # Remove __pycache__
    while IFS= read -r -d '' dir; do
        rm -rf "$dir" 2>/dev/null && ((count++)) || true
    done < <(find . -type d -name "__pycache__" -print0 2>/dev/null)

    # Remove .pyc files
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    # Remove pytest cache
    rm -rf .pytest_cache 2>/dev/null || true
    rm -rf .coverage htmlcov 2>/dev/null || true

    # Remove logs
    rm -rf logs/*.log 2>/dev/null || true

    print_success "Removed $count cache directories"
    print_success "Removed pytest cache and coverage files"
}

run_quick_tests() {
    print_section "Running Quick Tests"

    clean_cache

    # Run fast tests only
    print_info "Running unit tests (skipping slow integration tests)..."
    echo ""

    python3 -m pytest "$TEST_DIR" \
        -v \
        -m "not slow" \
        --tb=short \
        -x \
        || {
            print_error "Tests failed"
            return 1
        }

    echo ""
    print_success "Quick tests passed!"
    return 0
}

run_full_tests() {
    print_section "Running Full Test Suite"

    clean_cache

    print_info "Running all tests with coverage..."
    echo ""

    python3 -m pytest "$TEST_DIR" \
        --cov=shared \
        --cov=web/backend \
        --cov-report=term-missing \
        --cov-report=html \
        -v \
        --tb=short \
        || {
            print_error "Tests failed"
            echo ""
            print_info "Coverage report: htmlcov/index.html"
            return 1
        }

    echo ""
    print_success "All tests passed!"
    print_info "Coverage report: htmlcov/index.html"
    return 0
}

start_backend() {
    print_section "Starting Backend"

    # Check port availability
    if command -v lsof &> /dev/null; then
        if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_error "Port $BACKEND_PORT is already in use"
            return 1
        fi
    fi

    # Ensure database is set up
    export USE_SQLITE=true

    # Start backend
    cd "$BACKEND_DIR"
    python3 app.py > ../../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    cd ../..

    # Wait and verify
    sleep 2
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend failed to start"
        tail -20 logs/backend.log
        return 1
    fi

    print_success "Backend running on http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)"
    return 0
}

start_frontend() {
    print_section "Starting Frontend"

    # Check port availability
    if command -v lsof &> /dev/null; then
        if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_error "Port $FRONTEND_PORT is already in use"
            return 1
        fi
    fi

    # Start frontend
    cd "$FRONTEND_DIR"
    python3 -m http.server $FRONTEND_PORT > ../../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ../..

    # Wait and verify
    sleep 1
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend failed to start"
        return 1
    fi

    print_success "Frontend running on http://localhost:$FRONTEND_PORT (PID: $FRONTEND_PID)"
    return 0
}

start_dev_servers() {
    print_section "Starting Development Servers"

    # Create logs directory
    mkdir -p logs

    # Start both servers
    start_backend || return 1
    start_frontend || return 1

    echo ""
    echo -e "${GREEN}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║                    Servers Running!                        ║${NC}"
    echo -e "${GREEN}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${BOLD}Frontend:${NC}  ${CYAN}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "  ${BOLD}Backend:${NC}   ${CYAN}http://localhost:$BACKEND_PORT${NC}"
    echo -e "  ${BOLD}API Health:${NC} ${CYAN}http://localhost:$BACKEND_PORT/api/health${NC}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""

    # Open browser
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:$FRONTEND_PORT" 2>/dev/null &
    elif command -v open &> /dev/null; then
        open "http://localhost:$FRONTEND_PORT" 2>/dev/null &
    fi

    # Monitor
    while true; do
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            print_error "Backend crashed!"
            tail -20 logs/backend.log
            break
        fi

        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend crashed!"
            break
        fi

        sleep 2
    done
}

show_menu() {
    print_header

    echo -e "${BOLD}Quick Actions:${NC}"
    echo ""
    echo -e "  ${GREEN}1${NC}) Run Quick Tests         ${CYAN}(fast unit tests)${NC}"
    echo -e "  ${GREEN}2${NC}) Run Full Test Suite    ${CYAN}(with coverage)${NC}"
    echo -e "  ${GREEN}3${NC}) Start Dev Servers      ${CYAN}(backend + frontend)${NC}"
    echo -e "  ${GREEN}4${NC}) Check Dependencies"
    echo -e "  ${GREEN}5${NC}) Clean Cache & Logs"
    echo -e "  ${GREEN}6${NC}) Run Database Migrations"
    echo -e "  ${GREEN}7${NC}) View Test Coverage Report"
    echo ""
    echo -e "  ${YELLOW}F${NC}) Full Launcher          ${CYAN}(./tools/launch.sh)${NC}"
    echo -e "  ${RED}0${NC}) Exit"
    echo ""
    echo -ne "${BOLD}Select [0-7/F]:${NC} "
}

run_migrations() {
    print_section "Database Migrations"

    export USE_SQLITE=true

    if ! command -v alembic &> /dev/null; then
        print_warning "Alembic not installed"
        pip install alembic
    fi

    print_info "Running migrations..."
    cd migrations
    alembic upgrade head
    cd ..

    print_success "Database up to date"
}

view_coverage() {
    if [ -f "htmlcov/index.html" ]; then
        print_info "Opening coverage report..."

        if command -v xdg-open &> /dev/null; then
            xdg-open htmlcov/index.html
        elif command -v open &> /dev/null; then
            open htmlcov/index.html
        else
            print_info "Coverage report: htmlcov/index.html"
        fi
    else
        print_warning "No coverage report found"
        echo "Run full tests first (option 2)"
    fi
}

###############################################################################
# Main Program
###############################################################################

main() {
    # Handle command line arguments
    case "${1:-menu}" in
        test|tests)
            print_header
            run_full_tests
            exit $?
            ;;
        quick)
            print_header
            run_quick_tests
            exit $?
            ;;
        dev|start|serve)
            print_header
            check_dependencies
            start_dev_servers
            exit $?
            ;;
        clean)
            print_header
            clean_cache
            echo ""
            print_success "Cleanup complete"
            exit 0
            ;;
        deps|dependencies)
            print_header
            check_dependencies
            exit $?
            ;;
        migrate|migrations)
            print_header
            run_migrations
            exit $?
            ;;
        coverage|cov)
            view_coverage
            exit $?
            ;;
        help|-h|--help)
            print_header
            echo "Usage: ./run.sh [command]"
            echo ""
            echo "Commands:"
            echo "  test       Run full test suite with coverage"
            echo "  quick      Run quick tests (no coverage)"
            echo "  dev        Start development servers"
            echo "  clean      Clean cache and temp files"
            echo "  deps       Check and install dependencies"
            echo "  migrate    Run database migrations"
            echo "  coverage   View coverage report"
            echo "  help       Show this help"
            echo ""
            echo "No command: Interactive menu"
            exit 0
            ;;
        menu|*)
            # Interactive menu
            while true; do
                show_menu
                read -r choice

                case $choice in
                    1)
                        print_header
                        run_quick_tests
                        echo ""
                        echo -ne "Press Enter to continue..."
                        read -r
                        ;;
                    2)
                        print_header
                        run_full_tests
                        echo ""
                        echo -ne "Press Enter to continue..."
                        read -r
                        ;;
                    3)
                        print_header
                        check_dependencies
                        start_dev_servers
                        ;;
                    4)
                        print_header
                        check_dependencies
                        echo ""
                        echo -ne "Press Enter to continue..."
                        read -r
                        ;;
                    5)
                        print_header
                        clean_cache
                        echo ""
                        echo -ne "Press Enter to continue..."
                        read -r
                        ;;
                    6)
                        print_header
                        run_migrations
                        echo ""
                        echo -ne "Press Enter to continue..."
                        read -r
                        ;;
                    7)
                        view_coverage
                        sleep 2
                        ;;
                    [Ff])
                        print_header
                        print_info "Launching full launcher..."
                        sleep 1
                        ./tools/launch.sh
                        ;;
                    0)
                        cleanup
                        ;;
                    *)
                        print_error "Invalid option"
                        sleep 1
                        ;;
                esac
            done
            ;;
    esac
}

# Run main program
main "$@"
