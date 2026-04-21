#!/bin/bash

################################################################################
# Social Pulse - Quick Commands Reference
#
# This script provides quick access to common Social Pulse commands
#
# Usage: ./social_pulse.sh [COMMAND] [OPTIONS]
#
# Commands:
#   deploy          Run full deployment
#   start           Start all services
#   stop            Stop all services
#   status          Check service status
#   logs            View service logs
#   rebuild         Rebuild shared library
#   migrate         Run database migrations
#   clean           Clean up deployment
#   help            Show this help message
#
################################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Color codes
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

show_help() {
    cat <<EOF
${BLUE}Social Pulse - Quick Commands${NC}

Usage: ./social_pulse.sh [COMMAND] [OPTIONS]

Commands:
  ${GREEN}deploy${NC}          Full deployment of Social Pulse
                   Options: --clean, --shared-only, --skip-db

  ${GREEN}start${NC}           Start all services
                   Options: --background, --analysis-only, --report-only, --with-ui

  ${GREEN}stop${NC}            Stop all services
                   Options: --full-cleanup, --kill-pypi

  ${GREEN}status${NC}          Check service status

  ${GREEN}logs${NC}            View service logs
                   Options: --analysis, --report, --pypi, --follow

  ${GREEN}rebuild${NC}         Rebuild shared library

  ${GREEN}migrate${NC}         Run database migrations

  ${GREEN}clean${NC}           Clean up deployment

  ${GREEN}help${NC}            Show this help message

Examples:
  ./social_pulse.sh deploy
  ./social_pulse.sh deploy --clean
  ./social_pulse.sh start --background
  ./social_pulse.sh logs --follow
  ./social_pulse.sh rebuild
  ./social_pulse.sh status

EOF
}

check_service() {
    local port=$1
    local name=$2

    if curl -s http://localhost:$port/docs >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name (http://localhost:$port)"
    else
        echo -e "${YELLOW}✗${NC} $name (not responding on port $port)"
    fi
}

main() {
    case "${1:-help}" in
        deploy)
            shift
            "$SCRIPT_DIR/deploy_local.sh" "$@"
            ;;

        start)
            shift
            "$SCRIPT_DIR/start_local_services.sh" "$@"
            ;;

        stop)
            shift
            "$SCRIPT_DIR/stop_local_services.sh" "$@"
            ;;

        status)
            echo -e "${BLUE}Service Status${NC}"
            echo ""
            check_service 8080 "Analysis Service"
            check_service 8008 "Report Service"
            check_service 9002 "Report UI"
            check_service 3322 "PyPI Server"
            check_service 8081 "Poller"
            echo ""
            ;;

        logs)
            shift
            case "${1:-all}" in
                analysis)
                    tail "${2:--f}" "$PROJECT_ROOT/.analysis_service.log"
                    ;;
                report)
                    tail "${2:--f}" "$PROJECT_ROOT/.report_service.log"
                    ;;
                pypi)
                    tail "${2:--f}" "$HOME/.social_pulse/packages/pypiserver.log"
                    ;;
                follow)
                    echo -e "${BLUE}Following all logs (Ctrl+C to stop)${NC}"
                    tail -f \
                        "$PROJECT_ROOT/.analysis_service.log" \
                        "$PROJECT_ROOT/.report_service.log" \
                        "$HOME/.social_pulse/packages/pypiserver.log"
                    ;;
                all)
                    echo "Analysis Service Log:"
                    tail -n 20 "$PROJECT_ROOT/.analysis_service.log"
                    echo ""
                    echo "Report Service Log:"
                    tail -n 20 "$PROJECT_ROOT/.report_service.log"
                    echo ""
                    echo "PyPI Server Log:"
                    tail -n 20 "$HOME/.social_pulse/packages/pypiserver.log"
                    ;;
                *)
                    echo "Usage: ./social_pulse.sh logs [analysis|report|pypi|follow|all]"
                    ;;
            esac
            ;;

        rebuild)
            shift
            "$SCRIPT_DIR/deploy_local.sh" --force-rebuild --shared-only "$@"
            ;;

        migrate)
            echo -e "${BLUE}Running Database Migrations${NC}"
            echo ""

            # Analysis Service
            echo "Migrating Analysis Service database..."
            cd "$PROJECT_ROOT/services/analysis_service"
            if [ -f ".venv/bin/activate" ]; then
                source .venv/bin/activate
                yoyo apply || echo -e "${YELLOW}Migration may have already been applied${NC}"
                deactivate
            else
                echo -e "${YELLOW}Analysis Service not set up${NC}"
            fi

            echo ""

            # Report Service
            echo "Migrating Report Service database..."
            cd "$PROJECT_ROOT/services/report_service"
            if [ -f ".venv/bin/activate" ]; then
                source .venv/bin/activate
                yoyo apply || echo -e "${YELLOW}Migration may have already been applied${NC}"
                deactivate
            else
                echo -e "${YELLOW}Report Service not set up${NC}"
            fi
            ;;

        clean)
            shift
            "$SCRIPT_DIR/stop_local_services.sh" --full-cleanup
            ;;

        help|--help|-h)
            show_help
            ;;

        *)
            echo -e "${YELLOW}Unknown command: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
