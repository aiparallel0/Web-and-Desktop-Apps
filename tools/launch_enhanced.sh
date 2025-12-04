#!/bin/bash
###############################################################################
# Receipt Extractor - Enhanced Unified Launcher Script v3.1
#
# Circular Exchange Framework Integration:
# -----------------------------------------
# Module ID: scripts.launch_enhanced
# Description: Enhanced launcher with metrics tracking, ASCII visualizations,
#              and comprehensive performance monitoring
# Dependencies: [check_dependencies.py, run_all_tests.py]
# Exports: [quick_launch, full_launch, run_tests, check_gpu_status,
#           clean_python_cache, show_metrics_dashboard]
#
# New Features in v3.1:
# - Performance metrics tracking (execution time, resource usage)
# - ASCII-based data visualizations (bar charts, pie charts, line graphs)
# - System resource monitoring (CPU, memory, disk usage)
# - Success/failure rate tracking
# - Comprehensive metrics dashboard
# - Pseudo-3D ASCII charts using box-drawing characters
#
# Usage: ./launch_enhanced.sh [option]
#   No option: Interactive menu with metrics dashboard
#   --quick: Quick launch (skip tests)
#   --test:  Run tests only
#   --clean: Clean cache only
#   --metrics: Show metrics dashboard only
#
# Cross-platform compatible: Git Bash, CMD, Unix terminals
# NO EMOJI CHARACTERS - Uses only ASCII and box-drawing characters
###############################################################################

set -e

# Colors and formatting (optional - degrades gracefully)
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
BACKEND_DIR="web/backend"
FRONTEND_DIR="web/frontend"
LOG_DIR="logs"
METRICS_DIR="logs/metrics"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$LOG_DIR/test-reports"
mkdir -p "$METRICS_DIR"

# Global state variables
BACKEND_PID=""
FRONTEND_PID=""
TESTS_PASSED=false
DEPS_CHECKED=false
GPU_AVAILABLE=false

###############################################################################
# Metrics Tracking System
###############################################################################

# Metrics storage
declare -A OPERATION_TIMES
declare -A OPERATION_STATUS
declare -A OPERATION_START_TIMES
declare -A RESOURCE_SNAPSHOTS
TOTAL_OPERATIONS=0
SUCCESSFUL_OPERATIONS=0
FAILED_OPERATIONS=0
SESSION_START_TIME=$(date +%s)

# Metrics file
METRICS_FILE="$METRICS_DIR/session_$(date +%Y%m%d_%H%M%S).metrics"

# Initialize metrics file
init_metrics() {
    cat > "$METRICS_FILE" <<EOF
# Receipt Extractor - Performance Metrics
# Session Start: $(date '+%Y-%m-%d %H:%M:%S')
#
# Format: OPERATION|STATUS|DURATION_MS|TIMESTAMP
EOF
}

# Start timing an operation
start_operation() {
    local op_name="$1"
    OPERATION_START_TIMES["$op_name"]=$(date +%s%3N)
}

# End timing an operation
end_operation() {
    local op_name="$1"
    local status="$2"  # SUCCESS or FAILURE
    local start_time="${OPERATION_START_TIMES[$op_name]}"
    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    OPERATION_TIMES["$op_name"]=$duration
    OPERATION_STATUS["$op_name"]=$status

    # Update counters
    ((TOTAL_OPERATIONS++))
    if [ "$status" = "SUCCESS" ]; then
        ((SUCCESSFUL_OPERATIONS++))
    else
        ((FAILED_OPERATIONS++))
    fi

    # Log to metrics file
    echo "$op_name|$status|$duration|$(date +%s)" >> "$METRICS_FILE"
}

# Capture system resource snapshot
capture_resource_snapshot() {
    local snapshot_name="$1"
    local cpu_usage=""
    local mem_usage=""
    local disk_usage=""

    # CPU usage (if available)
    if command -v top &> /dev/null; then
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}' 2>/dev/null || echo "N/A")
    elif command -v ps &> /dev/null; then
        cpu_usage=$(ps -A -o %cpu | awk '{s+=$1} END {print s"%"}' 2>/dev/null || echo "N/A")
    else
        cpu_usage="N/A"
    fi

    # Memory usage
    if command -v free &> /dev/null; then
        mem_usage=$(free | awk '/Mem:/ {printf "%.1f%%", $3/$2 * 100.0}' 2>/dev/null || echo "N/A")
    elif command -v vm_stat &> /dev/null; then
        # macOS
        mem_usage=$(vm_stat | awk '/Pages active/ {printf "~%.0f%%", $3/250}' 2>/dev/null || echo "N/A")
    else
        mem_usage="N/A"
    fi

    # Disk usage
    if command -v df &> /dev/null; then
        disk_usage=$(df -h . | awk 'NR==2 {print $5}' 2>/dev/null || echo "N/A")
    else
        disk_usage="N/A"
    fi

    RESOURCE_SNAPSHOTS["${snapshot_name}_CPU"]="$cpu_usage"
    RESOURCE_SNAPSHOTS["${snapshot_name}_MEM"]="$mem_usage"
    RESOURCE_SNAPSHOTS["${snapshot_name}_DISK"]="$disk_usage"
}

###############################################################################
# ASCII Visualization Functions
###############################################################################

# Draw a horizontal bar chart
# Usage: draw_bar_chart <value> <max_value> <width> <label>
draw_bar_chart() {
    local value=$1
    local max_value=$2
    local width=${3:-50}
    local label="$4"

    local filled=$(awk "BEGIN {printf \"%.0f\", ($value / $max_value) * $width}")
    local empty=$((width - filled))

    # Ensure non-negative
    if [ $filled -lt 0 ]; then filled=0; fi
    if [ $empty -lt 0 ]; then empty=0; fi

    local percentage=$(awk "BEGIN {printf \"%.1f\", ($value / $max_value) * 100}")

    echo -n "  $label "
    echo -n "["

    # Draw filled portion with gradient effect
    for ((i=0; i<filled; i++)); do
        if [ $((i % 4)) -eq 0 ]; then
            echo -ne "${GREEN}█${NC}"
        elif [ $((i % 4)) -eq 1 ]; then
            echo -ne "${GREEN}▓${NC}"
        elif [ $((i % 4)) -eq 2 ]; then
            echo -ne "${GREEN}▒${NC}"
        else
            echo -ne "${GREEN}░${NC}"
        fi
    done

    # Draw empty portion
    for ((i=0; i<empty; i++)); do
        echo -n " "
    done

    echo -e "] ${BOLD}${percentage}%${NC}"
}

# Draw a vertical bar chart
# Usage: draw_vertical_bars <label1> <value1> <label2> <value2> ...
draw_vertical_bars() {
    local -a labels=()
    local -a values=()
    local max_value=0
    local chart_height=10

    # Parse arguments
    while [ $# -gt 0 ]; do
        labels+=("$1")
        values+=("$2")
        if [ "$2" -gt "$max_value" ]; then
            max_value=$2
        fi
        shift 2
    done

    # Ensure max_value is not zero
    if [ "$max_value" -eq 0 ]; then
        max_value=1
    fi

    echo ""
    # Draw chart from top to bottom
    for ((row=chart_height; row>=0; row--)); do
        echo -n "  "

        # Y-axis label
        local threshold=$(awk "BEGIN {printf \"%.0f\", ($row / $chart_height) * $max_value}")
        printf "%4d │" $threshold

        # Draw bars
        for ((i=0; i<${#values[@]}; i++)); do
            local bar_height=$(awk "BEGIN {printf \"%.0f\", (${values[$i]} / $max_value) * $chart_height}")

            if [ $bar_height -ge $row ]; then
                echo -ne " ${GREEN}███${NC} "
            else
                echo -n "     "
            fi
        done
        echo ""
    done

    # Draw x-axis
    echo -n "       └"
    for ((i=0; i<${#values[@]}; i++)); do
        echo -n "─────"
    done
    echo ""

    # Draw labels
    echo -n "        "
    for ((i=0; i<${#labels[@]}; i++)); do
        printf " %-3s " "${labels[$i]}"
    done
    echo ""
}

# Draw a pseudo-3D pie chart
# Usage: draw_pie_chart <label1> <value1> <label2> <value2> ...
draw_pie_chart() {
    local -a labels=()
    local -a values=()
    local total=0

    # Parse arguments
    while [ $# -gt 0 ]; do
        labels+=("$1")
        values+=("$2")
        total=$((total + $2))
        shift 2
    done

    if [ "$total" -eq 0 ]; then
        echo "  No data to display"
        return
    fi

    echo ""
    echo "       ╭─────────────────────╮"
    echo "      ╱                       ╲"
    echo "     ╱                         ╲"

    # Draw pie slices with pseudo-3D effect
    local current_angle=0
    local colors=("${GREEN}" "${BLUE}" "${CYAN}" "${MAGENTA}" "${YELLOW}")

    for ((i=0; i<${#values[@]}; i++)); do
        local percentage=$(awk "BEGIN {printf \"%.1f\", (${values[$i]} / $total) * 100}")
        local color_idx=$((i % ${#colors[@]}))
        local color="${colors[$color_idx]}"

        # Create visual representation
        if [ "$i" -eq 0 ]; then
            echo -e "    ${color}│${NC}  ${BOLD}${labels[$i]}${NC} (${percentage}%)"
            echo -e "    ${color}│${NC}  ████████████"
        else
            echo -e "    ${color}├──${NC} ${BOLD}${labels[$i]}${NC} (${percentage}%)"
            echo -e "    ${color}│${NC}  ▓▓▓▓▓▓▓▓"
        fi
    done

    echo "     ╲                         ╱"
    echo "      ╲                       ╱"
    echo "       ╰─────────────────────╯"
    echo ""
}

# Draw a simple line graph (sparkline style)
# Usage: draw_line_graph <value1> <value2> <value3> ...
draw_line_graph() {
    local -a values=("$@")
    local max_val=0
    local min_val=999999

    # Find min and max
    for val in "${values[@]}"; do
        if [ "$val" -gt "$max_val" ]; then max_val=$val; fi
        if [ "$val" -lt "$min_val" ]; then min_val=$val; fi
    done

    local range=$((max_val - min_val))
    if [ "$range" -eq 0 ]; then range=1; fi

    local height=8
    local chart=()

    # Initialize chart array
    for ((i=0; i<=height; i++)); do
        chart[$i]=""
    done

    # Plot values
    for val in "${values[@]}"; do
        local normalized=$(awk "BEGIN {printf \"%.0f\", (($val - $min_val) / $range) * $height}")

        for ((row=0; row<=height; row++)); do
            if [ $row -eq $((height - normalized)) ]; then
                chart[$row]+="${GREEN}●─${NC}"
            elif [ $row -lt $((height - normalized)) ]; then
                chart[$row]+="  "
            else
                chart[$row]+="  "
            fi
        done
    done

    # Draw chart
    echo ""
    for ((row=0; row<=height; row++)); do
        local threshold=$(awk "BEGIN {printf \"%.0f\", $max_val - (($row / $height) * $range)}")
        printf "  %5d │ %s\n" $threshold "${chart[$row]}"
    done

    # Draw x-axis
    echo -n "        └"
    for ((i=0; i<${#values[@]}; i++)); do
        echo -n "──"
    done
    echo ""
}

# Draw a progress bar with percentage
# Usage: draw_progress_bar <current> <total> <width>
draw_progress_bar() {
    local current=$1
    local total=$2
    local width=${3:-50}

    local filled=$(awk "BEGIN {printf \"%.0f\", ($current / $total) * $width}")
    local empty=$((width - filled))
    local percentage=$(awk "BEGIN {printf \"%.1f\", ($current / $total) * 100}")

    echo -n "  Progress: ["

    # Draw filled portion
    for ((i=0; i<filled; i++)); do
        echo -ne "${CYAN}█${NC}"
    done

    # Draw empty portion
    for ((i=0; i<empty; i++)); do
        echo -ne "${DIM}░${NC}"
    done

    echo -e "] ${BOLD}${percentage}%${NC} (${current}/${total})"
}

###############################################################################
# UI Functions with Enhanced Visuals
###############################################################################

print_banner() {
    clear
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                    ║"
    echo "║     Receipt Extractor - Enhanced Unified Launcher v3.1             ║"
    echo "║                                                                    ║"
    echo "║   AI-Powered Receipt Processing with Performance Metrics          ║"
    echo "║                                                                    ║"
    echo "╚════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_separator() {
    echo -e "${DIM}────────────────────────────────────────────────────────────────────${NC}"
}

print_double_separator() {
    echo -e "${BOLD}════════════════════════════════════════════════════════════════════${NC}"
}

print_section() {
    echo ""
    echo -e "${BOLD}${BLUE}┌─ $1 ─┐${NC}"
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

print_metric() {
    local label="$1"
    local value="$2"
    local unit="$3"
    printf "  ${BOLD}%-30s${NC} ${GREEN}%s${NC} %s\n" "$label:" "$value" "$unit"
}

show_menu() {
    print_banner

    # Show quick metrics summary
    echo -e "${BOLD}${CYAN}┌─ Quick Status ─────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC}"
    if [ "$TESTS_PASSED" = true ]; then
        echo -e "${CYAN}│${NC}  Tests:        ${GREEN}PASSED${NC}"
    else
        echo -e "${CYAN}│${NC}  Tests:        ${YELLOW}NOT RUN${NC}"
    fi

    if [ "$DEPS_CHECKED" = true ]; then
        echo -e "${CYAN}│${NC}  Dependencies: ${GREEN}VERIFIED${NC}"
    else
        echo -e "${CYAN}│${NC}  Dependencies: ${YELLOW}NOT CHECKED${NC}"
    fi

    if [ -n "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${CYAN}│${NC}  Backend:      ${GREEN}RUNNING${NC} (PID: $BACKEND_PID)"
    else
        echo -e "${CYAN}│${NC}  Backend:      ${YELLOW}STOPPED${NC}"
    fi

    echo -e "${CYAN}│${NC}"
    echo -e "${BOLD}${CYAN}└────────────────────────────────────────────────────────────────┘${NC}"

    echo ""
    echo -e "${BOLD}Main Menu:${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} Quick Launch (Skip Tests)"
    echo -e "  ${GREEN}2)${NC} Full Launch (With Tests & Validation)"
    echo -e "  ${GREEN}3)${NC} Run Tests Only"
    echo -e "  ${GREEN}4)${NC} Check & Install Dependencies"
    echo -e "  ${GREEN}5)${NC} Check GPU Status"
    echo -e "  ${GREEN}6)${NC} System Health Report"
    echo -e "  ${GREEN}7)${NC} Clean Cache (Python bytecode & pytest)"
    echo -e "  ${GREEN}8)${NC} Run Database Migrations"
    echo -e "  ${GREEN}9)${NC} View Logs"
    echo -e "  ${CYAN}M)${NC} Metrics Dashboard (Performance Analytics)"
    echo -e "  ${GREEN}H)${NC} Help & Documentation"
    echo -e "  ${CYAN}E)${NC} Export System Report for AI Analysis"
    echo -e "  ${RED}0)${NC} Exit"
    echo ""
    echo -ne "${BOLD}Select an option [0-9/M/H/E]:${NC} "
}

###############################################################################
# Metrics Dashboard
###############################################################################

show_metrics_dashboard() {
    print_banner
    print_section "Performance Metrics Dashboard"

    capture_resource_snapshot "dashboard"

    local session_duration=$(($(date +%s) - SESSION_START_TIME))
    local session_minutes=$((session_duration / 60))
    local session_seconds=$((session_duration % 60))

    echo ""
    echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║                    SESSION SUMMARY                                ║${NC}"
    echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    print_metric "Session Duration" "${session_minutes}m ${session_seconds}s" ""
    print_metric "Total Operations" "$TOTAL_OPERATIONS" "operations"
    print_metric "Successful Operations" "$SUCCESSFUL_OPERATIONS" "operations"
    print_metric "Failed Operations" "$FAILED_OPERATIONS" "operations"

    if [ "$TOTAL_OPERATIONS" -gt 0 ]; then
        local success_rate=$(awk "BEGIN {printf \"%.1f\", ($SUCCESSFUL_OPERATIONS / $TOTAL_OPERATIONS) * 100}")
        print_metric "Success Rate" "$success_rate" "%"
    fi

    echo ""
    echo -e "${BOLD}${YELLOW}┌─ System Resources ─────────────────────────────────────────────┐${NC}"
    echo -e "${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  CPU Usage:    ${RESOURCE_SNAPSHOTS[dashboard_CPU]}"
    echo -e "${YELLOW}│${NC}  Memory Usage: ${RESOURCE_SNAPSHOTS[dashboard_MEM]}"
    echo -e "${YELLOW}│${NC}  Disk Usage:   ${RESOURCE_SNAPSHOTS[dashboard_DISK]}"
    echo -e "${YELLOW}│${NC}"
    echo -e "${BOLD}${YELLOW}└────────────────────────────────────────────────────────────────┘${NC}"

    # Show operation timings if any
    if [ ${#OPERATION_TIMES[@]} -gt 0 ]; then
        echo ""
        echo -e "${BOLD}${MAGENTA}┌─ Operation Performance ────────────────────────────────────────┐${NC}"
        echo ""

        # Find max time for scaling
        local max_time=1
        for time in "${OPERATION_TIMES[@]}"; do
            if [ "$time" -gt "$max_time" ]; then
                max_time=$time
            fi
        done

        # Display each operation with bar chart
        for op in "${!OPERATION_TIMES[@]}"; do
            local time="${OPERATION_TIMES[$op]}"
            local status="${OPERATION_STATUS[$op]}"
            local status_icon="[OK]"
            local status_color="${GREEN}"

            if [ "$status" != "SUCCESS" ]; then
                status_icon="[FAIL]"
                status_color="${RED}"
            fi

            echo -e "  ${BOLD}${op}${NC} ${status_color}${status_icon}${NC}"
            draw_bar_chart "$time" "$max_time" 50 "$(printf '%8s ms' $time)"
            echo ""
        done

        echo -e "${BOLD}${MAGENTA}└────────────────────────────────────────────────────────────────┘${NC}"
    fi

    # Success/Failure pie chart
    if [ "$TOTAL_OPERATIONS" -gt 0 ]; then
        echo ""
        echo -e "${BOLD}${CYAN}Operation Success Rate:${NC}"
        draw_pie_chart "Success" "$SUCCESSFUL_OPERATIONS" "Failed" "$FAILED_OPERATIONS"
    fi

    # Show historical data if metrics file exists
    if [ -f "$METRICS_FILE" ] && [ -s "$METRICS_FILE" ]; then
        echo ""
        echo -e "${BOLD}${BLUE}Session Metrics Trend:${NC}"

        # Parse last 10 operations for trend
        local -a trend_values=()
        while IFS='|' read -r op status duration ts; do
            if [[ "$op" != \#* ]]; then
                trend_values+=("$duration")
            fi
        done < <(tail -n 10 "$METRICS_FILE")

        if [ ${#trend_values[@]} -gt 0 ]; then
            draw_line_graph "${trend_values[@]}"
        fi
    fi

    echo ""
    echo -ne "${BOLD}Press Enter to continue...${NC}"
    read -r
}

###############################################################################
# Cache Cleaning Functions (with metrics)
###############################################################################

clean_python_cache() {
    print_section "Cleaning Python Cache"
    start_operation "cache_clean"
    capture_resource_snapshot "pre_clean"

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

    capture_resource_snapshot "post_clean"
    end_operation "cache_clean" "SUCCESS"

    print_success "Removed $pycache_count __pycache__ directories"
    print_success "Removed $pyc_count .pyc files"
    print_info "Cache cleanup complete - tests will use fresh code"

    # Show progress visualization
    echo ""
    draw_progress_bar $((pycache_count + pyc_count)) $((pycache_count + pyc_count + 1)) 40
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

    # Show final metrics
    local session_duration=$(($(date +%s) - SESSION_START_TIME))
    echo ""
    print_double_separator
    echo -e "${BOLD}${CYAN}Session Statistics:${NC}"
    print_metric "Total Duration" "$((session_duration / 60))m $((session_duration % 60))s" ""
    print_metric "Operations Completed" "$TOTAL_OPERATIONS" ""
    print_metric "Success Rate" "$(awk "BEGIN {if ($TOTAL_OPERATIONS > 0) printf \"%.1f\", ($SUCCESSFUL_OPERATIONS / $TOTAL_OPERATIONS) * 100; else print \"N/A\"}")%" ""
    print_double_separator

    echo ""
    echo -e "${GREEN}${BOLD}Cleanup complete. Thank you for using Receipt Extractor!${NC}"
    echo -e "${DIM}Metrics saved to: $METRICS_FILE${NC}"
    exit 0
}

# Set up trap to catch Ctrl+C
trap cleanup SIGINT SIGTERM

###############################################################################
# System Checks (with metrics)
###############################################################################

check_python() {
    print_section "Python Environment Check"
    start_operation "python_check"
    capture_resource_snapshot "python_check"

    if ! command -v python3 &> /dev/null; then
        if ! command -v python &> /dev/null; then
            print_error "Python 3 is not installed"
            echo "Please install Python 3.8 or higher"
            end_operation "python_check" "FAILURE"
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
        end_operation "python_check" "FAILURE"
        return 1
    fi

    print_success "pip available"
    end_operation "python_check" "SUCCESS"
    return 0
}

check_directories() {
    print_section "Directory Structure Validation"
    start_operation "directory_check"

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
        end_operation "directory_check" "SUCCESS"
        return 0
    else
        end_operation "directory_check" "FAILURE"
        return 1
    fi
}

check_ports() {
    print_section "Port Availability Check"
    start_operation "port_check"

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
        end_operation "port_check" "SUCCESS"
        return 0
    else
        end_operation "port_check" "FAILURE"
        return 1
    fi
}

###############################################################################
# Advanced Features (with metrics)
###############################################################################

run_dependency_check() {
    print_section "Dependency Analysis"
    start_operation "dependency_check"

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
            end_operation "dependency_check" "SUCCESS"
            return 0
        else
            print_warning "Some dependencies may be missing"
            echo ""
            echo "You can:"
            echo "  1. Run 'python3 check_dependencies.py' interactively for more control"
            echo "  2. Install manually: pip install -r requirements.txt"
            end_operation "dependency_check" "FAILURE"
            return 1
        fi
    else
        print_warning "check_dependencies.py not found, using pip install"
        cd "$BACKEND_DIR"
        pip3 install -q -r requirements.txt 2>"../$LOG_DIR/pip-install.log"
        cd -
        DEPS_CHECKED=true
        end_operation "dependency_check" "SUCCESS"
        return 0
    fi
}

check_gpu_status() {
    print_section "GPU Detection & Configuration"
    start_operation "gpu_check"

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
            end_operation "gpu_check" "SUCCESS"
        else
            GPU_AVAILABLE=false
            print_warning "No GPU detected - models will run on CPU"
            end_operation "gpu_check" "SUCCESS"
        fi
    else
        print_warning "GPU check utility not found"
        GPU_AVAILABLE=false
        end_operation "gpu_check" "FAILURE"
    fi

    echo ""
    echo -ne "Press Enter to continue..."
    read -r
}

run_tests() {
    print_section "Running Test Suite"
    start_operation "test_suite"

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
            end_operation "test_suite" "SUCCESS"
            return 0
        else
            print_warning "Some tests failed"
            test_failed=true
        fi
    else
        # Run complete pytest suite including circular_exchange framework
        echo ""
        print_info "Running complete test suite with coverage..."
        print_info "Including: circular_exchange framework, shared modules, backend tests"

        $PYTHON_CMD -m pytest tests/ \
            --cov=shared --cov=web/backend \
            --cov-report=term-missing \
            --cov-report=html \
            -v --tb=short \
            2>&1 | tee "$LOG_DIR/test-reports/full-suite.log"

        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "Complete test suite passed"
            TESTS_PASSED=true
            ((passed_count++))
        else
            print_warning "Some tests failed"
            test_failed=true
        fi
        ((test_count++))
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
            end_operation "test_suite" "FAILURE"
            return 1
        fi
    fi

    TESTS_PASSED=true
    end_operation "test_suite" "SUCCESS"
    return 0
}

system_health_report() {
    print_section "System Health Report"
    start_operation "health_report"
    capture_resource_snapshot "health"

    local PYTHON_CMD
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    echo ""
    echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║              SYSTEM HEALTH REPORT                         ║${NC}"
    echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${BOLD}Environment:${NC}"
    print_metric "Python Version" "$($PYTHON_CMD --version 2>&1 | awk '{print $2}')" ""
    print_metric "Working Directory" "$SCRIPT_DIR/.." ""
    print_metric "Log Directory" "$LOG_DIR" ""

    echo ""
    echo -e "${BOLD}System Resources:${NC}"
    print_metric "CPU Usage" "${RESOURCE_SNAPSHOTS[health_CPU]}" ""
    print_metric "Memory Usage" "${RESOURCE_SNAPSHOTS[health_MEM]}" ""
    print_metric "Disk Usage" "${RESOURCE_SNAPSHOTS[health_DISK]}" ""

    echo ""
    echo -e "${BOLD}Component Status:${NC}"

    # Dependencies status
    if [ "$DEPS_CHECKED" = true ]; then
        echo -e "  Dependencies:     ${GREEN}[VERIFIED]${NC}"
        draw_bar_chart 100 100 30 ""
    else
        echo -e "  Dependencies:     ${YELLOW}[NOT CHECKED]${NC}"
        draw_bar_chart 0 100 30 ""
    fi

    # GPU status
    if [ "$GPU_AVAILABLE" = true ]; then
        echo -e "  GPU Acceleration: ${GREEN}[AVAILABLE]${NC}"
        draw_bar_chart 100 100 30 ""
    else
        echo -e "  GPU Acceleration: ${YELLOW}[CPU MODE]${NC}"
        draw_bar_chart 0 100 30 ""
    fi

    # Tests status
    if [ "$TESTS_PASSED" = true ]; then
        echo -e "  Tests:            ${GREEN}[PASSED]${NC}"
        draw_bar_chart 100 100 30 ""
    else
        echo -e "  Tests:            ${YELLOW}[NOT RUN]${NC}"
        draw_bar_chart 0 100 30 ""
    fi

    echo ""
    echo -e "${BOLD}Ports:${NC}"
    print_metric "Backend Port" "$BACKEND_PORT" ""
    print_metric "Frontend Port" "$FRONTEND_PORT" ""

    echo ""
    echo -e "${BOLD}Services Status:${NC}"
    if [ -n "$BACKEND_PID" ]; then
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo -e "  Backend:  ${GREEN}[RUNNING]${NC} (PID: $BACKEND_PID)"
        else
            echo -e "  Backend:  ${RED}[STOPPED]${NC}"
        fi
    else
        echo -e "  Backend:  ${YELLOW}[NOT STARTED]${NC}"
    fi

    if [ -n "$FRONTEND_PID" ]; then
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo -e "  Frontend: ${GREEN}[RUNNING]${NC} (PID: $FRONTEND_PID)"
        else
            echo -e "  Frontend: ${RED}[STOPPED]${NC}"
        fi
    else
        echo -e "  Frontend: ${YELLOW}[NOT STARTED]${NC}"
    fi

    end_operation "health_report" "SUCCESS"

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
    echo "  5) Metrics log"
    echo "  6) Back to main menu"
    echo ""
    echo -ne "Select log to view [1-6]: "
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
        5)
            if [ -f "$METRICS_FILE" ]; then
                less "$METRICS_FILE"
            else
                print_warning "Metrics log not found"
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
    echo "  ./launch_enhanced.sh            Interactive menu (default)"
    echo "  ./launch_enhanced.sh --quick    Quick launch (skip tests)"
    echo "  ./launch_enhanced.sh --test     Run tests only"
    echo "  ./launch_enhanced.sh --clean    Clean cache only"
    echo "  ./launch_enhanced.sh --metrics  Show metrics dashboard"
    echo ""
    echo -e "${BOLD}New in v3.1 - Performance Metrics:${NC}"
    echo "  ${GREEN}M)${NC} Metrics Dashboard - View comprehensive performance analytics"
    echo "     - Operation timing and success rates"
    echo "     - System resource monitoring"
    echo "     - ASCII visualizations (bar charts, pie charts, line graphs)"
    echo "     - Session statistics"
    echo ""
    echo -e "${BOLD}Menu Options:${NC}"
    echo "  ${GREEN}Quick Launch:${NC} Start app immediately without tests"
    echo "  ${GREEN}Full Launch:${NC} Run all checks and tests before starting"
    echo "  ${GREEN}Run Tests:${NC} Execute test suite without starting app"
    echo "  ${GREEN}Check Dependencies:${NC} Verify and install required packages"
    echo "  ${GREEN}Check GPU:${NC} Detect GPU availability for acceleration"
    echo "  ${GREEN}Health Report:${NC} View system status and diagnostics"
    echo "  ${GREEN}Clean Cache:${NC} Remove Python bytecode and test cache"
    echo "  ${CYAN}Metrics Dashboard:${NC} View performance metrics and visualizations"
    echo ""
    echo -e "${BOLD}Logs Location:${NC}"
    echo "  Application logs: $LOG_DIR/"
    echo "  Performance metrics: $METRICS_DIR/"
    echo ""
    echo -ne "Press Enter to continue..."
    read -r
}

###############################################################################
# Database Migration Functions
###############################################################################

run_migrations() {
    print_section "Database Migrations"
    start_operation "database_migrations"

    print_info "Running database migrations with Alembic..."

    # Export USE_SQLITE for development/testing
    export USE_SQLITE=true

    # Check if alembic is installed
    if ! command -v alembic &> /dev/null; then
        print_warning "Alembic not found, installing..."
        pip3 install -q alembic
    fi

    # Run migrations from the migrations directory
    cd migrations
    if alembic upgrade head 2>&1 | tee "../$LOG_DIR/migrations.log"; then
        print_success "Database migrations completed"
        cd ..
        end_operation "database_migrations" "SUCCESS"
        return 0
    else
        print_error "Database migrations failed"
        echo "Check logs/migrations.log for details"
        cd ..
        end_operation "database_migrations" "FAILURE"
        return 1
    fi
}

###############################################################################
# Launch Functions (with metrics)
###############################################################################

start_servers() {
    local skip_checks=$1
    start_operation "server_startup"

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

    # Run database migrations
    run_migrations || {
        print_warning "Migrations failed, but continuing..."
    }

    print_section "Starting Services"

    # Start backend
    print_info "Starting backend API server..."
    cd "$BACKEND_DIR"
    # Export USE_SQLITE for development/testing
    export USE_SQLITE=true
    $PYTHON_CMD app.py > "../$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    cd ..

    sleep 3

    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend failed to start"
        echo "Check logs/backend.log for details"
        tail -20 "$LOG_DIR/backend.log"
        end_operation "server_startup" "FAILURE"
        return 1
    fi

    print_success "Backend running on http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)"

    # Start frontend
    print_info "Starting frontend web server..."
    cd "$FRONTEND_DIR"
    $PYTHON_CMD -m http.server $FRONTEND_PORT > "../$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    cd ..

    sleep 2

    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend failed to start"
        echo "Check logs/frontend.log for details"
        kill $BACKEND_PID 2>/dev/null
        end_operation "server_startup" "FAILURE"
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

    # Success message with enhanced visuals
    echo ""
    echo -e "${GREEN}${BOLD}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║                                                                    ║${NC}"
    echo -e "${GREEN}${BOLD}║        Receipt Extractor is now running!                           ║${NC}"
    echo -e "${GREEN}${BOLD}║                                                                    ║${NC}"
    echo -e "${GREEN}${BOLD}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${BOLD}Frontend:${NC}  ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "  ${BOLD}Backend:${NC}   ${BLUE}http://localhost:$BACKEND_PORT${NC}"
    echo -e "  ${BOLD}API Docs:${NC}  ${BLUE}http://localhost:$BACKEND_PORT/api/health${NC}"
    echo ""
    echo -e "${YELLOW}${BOLD}Press Ctrl+C to stop all servers${NC}"
    echo ""
    echo -e "${DIM}Logs: logs/backend.log | logs/frontend.log${NC}"
    echo ""

    end_operation "server_startup" "SUCCESS"

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
    start_operation "export_report"

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

    # Capture current metrics
    capture_resource_snapshot "export"

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
        echo "- **Working Directory:** $(pwd)"
        echo ""

        echo "### Hardware Resources"
        echo "- **CPU Usage:** ${RESOURCE_SNAPSHOTS[export_CPU]}"
        echo "- **Memory Usage:** ${RESOURCE_SNAPSHOTS[export_MEM]}"
        echo "- **Disk Usage:** ${RESOURCE_SNAPSHOTS[export_DISK]}"
        echo ""

        echo "## Performance Metrics"
        echo ""
        echo "### Session Statistics"
        local session_duration=$(($(date +%s) - SESSION_START_TIME))
        echo "- **Session Duration:** $((session_duration / 60))m $((session_duration % 60))s"
        echo "- **Total Operations:** $TOTAL_OPERATIONS"
        echo "- **Successful Operations:** $SUCCESSFUL_OPERATIONS"
        echo "- **Failed Operations:** $FAILED_OPERATIONS"
        if [ "$TOTAL_OPERATIONS" -gt 0 ]; then
            local success_rate=$(awk "BEGIN {printf \"%.1f\", ($SUCCESSFUL_OPERATIONS / $TOTAL_OPERATIONS) * 100}")
            echo "- **Success Rate:** ${success_rate}%"
        fi
        echo ""

        if [ ${#OPERATION_TIMES[@]} -gt 0 ]; then
            echo "### Operation Timings"
            echo ""
            echo "| Operation | Status | Duration (ms) |"
            echo "|-----------|--------|---------------|"
            for op in "${!OPERATION_TIMES[@]}"; do
                echo "| $op | ${OPERATION_STATUS[$op]} | ${OPERATION_TIMES[$op]} |"
            done
            echo ""
        fi

        echo "## Test Results"
        echo ""
        if [ "$TESTS_PASSED" = true ]; then
            echo "**Overall Status:** PASSED"
        else
            echo "**Overall Status:** NOT RUN OR FAILED"
        fi
        echo ""

        echo "## Component Status"
        echo ""
        echo "- **Dependencies:** $(if [ "$DEPS_CHECKED" = true ]; then echo "VERIFIED"; else echo "NOT CHECKED"; fi)"
        echo "- **GPU Acceleration:** $(if [ "$GPU_AVAILABLE" = true ]; then echo "AVAILABLE"; else echo "NOT AVAILABLE"; fi)"
        echo "- **Tests:** $(if [ "$TESTS_PASSED" = true ]; then echo "PASSED"; else echo "NOT RUN"; fi)"
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

        if [ -f "$METRICS_FILE" ]; then
            echo "## Detailed Metrics Log"
            echo ""
            echo "\`\`\`"
            cat "$METRICS_FILE"
            echo "\`\`\`"
            echo ""
        fi

        echo "---"
        echo ""
        echo "**End of Report**"
        echo ""
        echo "This report was generated automatically by the Receipt Extractor Enhanced Launcher v3.1"
        echo "Use it with AI coding assistants like Claude Code for efficient debugging and development."

    } > "$report_file"

    end_operation "export_report" "SUCCESS"

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
    # Initialize metrics
    init_metrics
    capture_resource_snapshot "startup"

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
        --metrics)
            show_metrics_dashboard
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
                print_banner
                run_migrations
                echo ""
                echo -ne "Press Enter to continue..."
                read -r
                ;;
            9)
                view_logs
                ;;
            [Mm])
                show_metrics_dashboard
                ;;
            [Hh])
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
