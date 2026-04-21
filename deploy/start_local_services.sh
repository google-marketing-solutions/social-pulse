#!/bin/bash

################################################################################
# Social Pulse - Start Local Services
#
# Starts all Social Pulse services for local development
#
# Usage: ./start_local_services.sh [OPTIONS]
#
# Options:
#   --help              Show this help message
#   --analysis-only     Start only analysis service
#   --report-only       Start only report service
#   --with-ui           Also start the report UI
#
################################################################################

set -e

# Color codes
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICES_DIR="$PROJECT_ROOT/services"

# Defaults
ANALYSIS_ONLY=false
REPORT_ONLY=false
WITH_UI=false

# Function: Print colored output
log() {
    echo -e "${BLUE}[Services]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            head -n 21 "$0" | tail -n 18
            exit 0
            ;;
        --analysis-only)
            ANALYSIS_ONLY=true
            shift
            ;;
        --report-only)
            REPORT_ONLY=true
            shift
            ;;
        --with-ui)
            WITH_UI=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if PyPI server is running
check_pypi_server() {
    log "Checking PyPI server..."
    if ! lsof -Pi :3322 -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_error "PyPI server not running on port 3322"
        log_error "Start it with: ./deploy/deploy_local.sh"
        exit 1
    fi
    log_success "PyPI server is running"
}

# Re-install shared library
reinstall_shared_lib() {
    log "Re-installing shared library into service virtual env..."
    pip install \
        --quiet \
        --force-reinstall \
        --no-deps \
        --extra-index-url http://localhost:3322/simple \
        --trusted-host localhost \
        socialpulse-common
    log_success "Shared library re-installed"
}

# Start analysis service
start_analysis() {
    log "Starting Analysis Service..."

    cd "$SERVICES_DIR/analysis_service"

    if [ ! -f ".venv/bin/activate" ]; then
        log_error "Analysis Service not set up. Run: ./deploy/deploy_local.sh"
        exit 1
    fi

    if [ ! -f ".env" ]; then
        log_error ".env file not found. Configure it first."
        exit 1
    fi

    source .venv/bin/activate

    reinstall_shared_lib

    log "Starting in background..."
    nohup bash -c "cd src && APP_ENV=dev uvicorn api.runner_entry:app --reload --port=8080" \
        > "$PROJECT_ROOT/.analysis_service.log" 2>&1 &
    log_success "Analysis Service started in background (PID: $!)"
    log "Logs: $PROJECT_ROOT/.analysis_service.log"
}

# Start poller service
start_poller() {
    log "Starting Poller Service..."

    cd "$SERVICES_DIR/analysis_service"

    if [ ! -f ".venv/bin/activate" ]; then
        log_error "Analysis Service not set up. Run: ./deploy/deploy_local.sh"
        exit 1
    fi

    if [ ! -f ".env" ]; then
        log_error ".env file not found. Configure it first."
        exit 1
    fi

    source .venv/bin/activate

    log "Starting in background..."
    nohup bash -c "cd src && APP_ENV=dev uvicorn api.poller:app --reload --port=8081" \
        > "$PROJECT_ROOT/.poller_service.log" 2>&1 &
    log_success "Poller Service started in background (PID: $!)"
    log "Logs: $PROJECT_ROOT/.poller_service.log"
}

# Start report service
start_report() {
    log "Starting Report Service..."

    cd "$SERVICES_DIR/report_service"

    if [ ! -f ".venv/bin/activate" ]; then
        log_error "Report Service not set up. Run: ./deploy/deploy_local.sh"
        exit 1
    fi

    if [ ! -f ".env" ]; then
        log_error ".env file not found. Configure it first."
        exit 1
    fi

    source .venv/bin/activate

    reinstall_shared_lib

    log "Starting in background..."
    nohup bash -c "cd src && APP_ENV=dev uvicorn main:app --reload --port=8008" \
        > "$PROJECT_ROOT/.report_service.log" 2>&1 &
    log_success "Report Service started in background (PID: $!)"
    log "Logs: $PROJECT_ROOT/.report_service.log"
}

# Start report UI
start_ui() {
    log "Starting Report UI..."

    cd "$SERVICES_DIR/report_service/ui"

    log "Starting in background..."
    nohup bash -c "npm run dev" \
        > "$PROJECT_ROOT/.report_ui.log" 2>&1 &
    log_success "Report UI started in background (PID: $!)"
    log "Logs: $PROJECT_ROOT/.report_ui.log"
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════╗"
    echo "║   Social Pulse - Start Local Services      ║"
    echo "╚════════════════════════════════════════════╝"
    echo -e "${NC}"

    check_pypi_server

    # Determine which services to start
    if [[ "$REPORT_ONLY" != true ]]; then
        start_analysis
        start_poller
    fi

    if [[ "$ANALYSIS_ONLY" != true ]]; then
        start_report &
        sleep 2
    fi

    if [[ "$WITH_UI" == true ]]; then
        start_ui &
        sleep 2
    fi

    sleep 2
    echo ""
    echo -e "${GREEN}All services started in background${NC}"
    echo ""
    echo "Service URLs:"
    echo "  Analysis Service: http://localhost:8080/docs"
    echo "  Poller Service:   http://localhost:8081/docs"
    echo "  Report Service: http://localhost:8008/docs"
    if [[ "$WITH_UI" == true ]]; then
        echo "  Report UI: http://localhost:9002"
    fi
    echo ""
    echo "View logs:"
    echo "  tail -f ../.analysis_service.log"
    echo "  tail -f ../.poller_service.log"
    echo "  tail -f ../.report_service.log"
    if [[ "$WITH_UI" == true ]]; then
        echo "  tail -f ../.report_ui.log"
    fi
    echo ""
}

main
