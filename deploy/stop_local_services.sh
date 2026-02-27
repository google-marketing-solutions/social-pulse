#!/bin/bash

################################################################################
# Social Pulse - Stop Local Services
#
# Stops all Social Pulse services and cleanup
#
# Usage: ./stop_local_services.sh [OPTIONS]
#
# Options:
#   --help              Show this help message
#   --full-cleanup      Also stop PyPI server and remove environments
#   --kill-pypi         Kill PyPI server
#
################################################################################

# Color codes
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Defaults
FULL_CLEANUP=false
KILL_PYPI=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            head -n 20 "$0" | tail -n 17
            exit 0
            ;;
        --full-cleanup)
            FULL_CLEANUP=true
            KILL_PYPI=true
            shift
            ;;
        --kill-pypi)
            KILL_PYPI=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

log() {
    echo -e "${BLUE}[Services]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════╗"
echo "║   Social Pulse - Stop Local Services       ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"

# Kill services
log "Stopping services..."

# Kill analysis service
if pgrep -f "uvicorn api.runner_entry:app" > /dev/null 2>&1; then
    pkill -f "uvicorn api.runner_entry:app" || true
    log_success "Analysis Service stopped"
else
    log_warning "Analysis Service not running"
fi

# Kill report service
if pgrep -f "uvicorn main:app.*8008" > /dev/null 2>&1; then
    pkill -f "uvicorn main:app.*8008" || true
    log_success "Report Service stopped"
else
    log_warning "Report Service not running"
fi

# Kill report UI
if pgrep -f "npm run dev" > /dev/null 2>&1; then
    pkill -f "npm run dev" || true
    log_success "Report UI stopped"
else
    log_warning "Report UI not running"
fi

# Kill PyPI server
if [[ "$KILL_PYPI" == true ]]; then
    log "Stopping PyPI server..."
    if lsof -ti:3322 > /dev/null 2>&1; then
        lsof -ti:3322 | xargs kill -9 2>/dev/null || true
        sleep 1
        log_success "PyPI server stopped"
    else
        log_warning "PyPI server not running"
    fi
fi

# Full cleanup
if [[ "$FULL_CLEANUP" == true ]]; then
    log "Performing full cleanup..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

    # Remove log files
    rm -f "$PROJECT_ROOT/.analysis_service.log"
    rm -f "$PROJECT_ROOT/.report_service.log"
    rm -f "$PROJECT_ROOT/.report_ui.log"
    log_success "Log files removed"

    # Remove environments (optional)
    log_warning "To remove virtual environments, run:"
    log_warning "  rm -rf $PROJECT_ROOT/services/analysis_service/.venv"
    log_warning "  rm -rf $PROJECT_ROOT/services/report_service/.venv"
    log_warning "  rm -rf $PROJECT_ROOT/services/shared_lib/.venv"
fi

echo ""
log_success "All services stopped"
echo ""
