#!/bin/bash

################################################################################
# Social Pulse Local Deployment Script
#
# This script handles the complete local deployment of Social Pulse, including:
# - Building and deploying the shared library to a local PyPI server
# - Setting up the Analysis Service
# - Setting up the Report Service
# - Creating required PostgreSQL databases
#
# Usage: ./deploy_local.sh [OPTIONS]
#
# Options:
#   --help              Show this help message
#   --shared-only       Deploy only the shared library
#   --skip-db           Skip database creation
#   --skip-services     Skip service setup
#   --clean             Clean up all artifacts and databases before deployment (legacy: cleans all except UI)
#   --clean-all         Clean all components (shared lib, analysis, report, UI, PyPI, packages)
#   --clean-analysis    Clean only the analysis service virtual environment
#   --clean-report      Clean only the report service virtual environment
#   --clean-ui          Clean only the UI (node_modules, .next, ui_dev.log)
#   --clean-shared-lib  Clean only the shared library virtual environment
#   --force-rebuild     Force rebuild even if already deployed
#   --db-user USER      PostgreSQL user (default: social_pulse_user)
#   --db-password PASS  PostgreSQL password (default: prompted)
#   --db-host HOST      PostgreSQL host (default: localhost)
#   --db-port PORT      PostgreSQL port (default: 5432)
#   --pypi-port PORT    Local PyPI server port (default: 3322)
#
################################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICES_DIR="$PROJECT_ROOT/services"

# Default values
PYPISERVER_PORT=3322
PYPISERVER_VENV="$HOME/.social_pulse/venv/pypiserver"
PACKAGES_DIR="$HOME/.social_pulse/packages"
DB_USER="social_pulse_user"
DB_PASSWORD=""
DB_HOST="localhost"
DB_PORT="5432"
SHARED_LIB_VENV="$SERVICES_DIR/shared_lib/.venv"
ANALYSIS_VENV="$SERVICES_DIR/analysis_service/.venv"
REPORT_VENV="$SERVICES_DIR/report_service/.venv"

# Flags
SHARED_ONLY=false
SKIP_DB=false
SKIP_SERVICES=false
FORCE_REBUILD=false
CLEAN_FIRST=false

# Function: Print colored output
log() {
    echo -e "${BLUE}[Social Pulse]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Function: Print help
show_help() {
    head -n 29 "$0" | tail -n 23
}

# Function: Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help)
                show_help
                exit 0
                ;;
            --shared-only)
                SHARED_ONLY=true
                shift
                ;;
            --skip-db)
                SKIP_DB=true
                shift
                ;;
            --skip-services)
                SKIP_SERVICES=true
                shift
                ;;
            --clean)
                CLEAN_FIRST=true
                shift
                ;;
            --clean-all)
                CLEAN_ALL=true
                shift
                ;;
            --clean-shared-lib)
                CLEAN_SHARED_LIB=true
                shift
                ;;
            --clean-analysis)
                CLEAN_ANALYSIS=true
                shift
                ;;
            --clean-report)
                CLEAN_REPORT=true
                shift
                ;;
            --clean-ui)
                CLEAN_UI=true
                shift
                ;;
            --force-rebuild)
                FORCE_REBUILD=true
                shift
                ;;
            --db-user)
                DB_USER="$2"
                shift 2
                ;;
            --db-password)
                DB_PASSWORD="$2"
                shift 2
                ;;
            --db-host)
                DB_HOST="$2"
                shift 2
                ;;
            --db-port)
                DB_PORT="$2"
                shift 2
                ;;
            --pypi-port)
                PYPISERVER_PORT="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Function: Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    local missing=0

    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        missing=1
    else
        local python_version=$(python3 --version 2>&1 | awk '{print $2}')
        log_success "Python $python_version found"
    fi

    # Check pip
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        log_error "pip is not installed"
        missing=1
    else
        log_success "pip found"
    fi

    # Check PostgreSQL
    if ! command -v psql &> /dev/null; then
        log_warning "PostgreSQL client (psql) not found - database operations may fail"
        log_warning "Install PostgreSQL or connect to an existing PostgreSQL server"
    else
        log_success "PostgreSQL client found"
    fi

    if [[ $missing -eq 1 ]]; then
        log_error "Missing required prerequisites. Please install and try again."
        exit 1
    fi
}

# Function: Clean up previous deployments
cleanup_previous() {

    # If no clean flags, do nothing
    if [[ "$CLEAN_FIRST" != true && "$CLEAN_ALL" != true && "$CLEAN_ANALYSIS" != true && "$CLEAN_REPORT" != true && "$CLEAN_UI" != true ]]; then
        return
    fi

    # CLEAN_ALL: clean everything
    if [[ "$CLEAN_ALL" == true ]]; then
        log "Cleaning ALL components..."
        if lsof -Pi :$PYPISERVER_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_warning "Stopping PyPI server on port $PYPISERVER_PORT..."
            lsof -ti:$PYPISERVER_PORT | xargs kill -9 2>/dev/null || true
            sleep 1
        fi
        log_warning "Removing all virtual environments and packages..."
        rm -rf "$SHARED_LIB_VENV" "$ANALYSIS_VENV" "$REPORT_VENV" "$PYPISERVER_VENV"
        rm -rf "$PACKAGES_DIR"
        local ui_dir="$SERVICES_DIR/report_service/ui"
        rm -rf "$ui_dir/node_modules" "$ui_dir/.next" "$ui_dir/ui_dev.log"
        log_success "All components cleaned."
        return
    fi

    # CLEAN_SHARED_LIB: clean only shared lib venv
    if [[ "$CLEAN_SHARED_LIB" == true ]]; then
        log "Cleaning shared library virtual environment..."
        rm -rf "$SHARED_LIB_VENV"
        log_success "Shared library virtual environment cleaned."
    fi

    # CLEAN_ANALYSIS: clean only analysis venv
    if [[ "$CLEAN_ANALYSIS" == true ]]; then
        log "Cleaning analysis service..."
        rm -rf "$ANALYSIS_VENV"
        log_success "Analysis service cleaned."
    fi

    # CLEAN_REPORT: clean only report venv
    if [[ "$CLEAN_REPORT" == true ]]; then
        log "Cleaning report service..."
        rm -rf "$REPORT_VENV"
        log_success "Report service cleaned."
    fi

    # CLEAN_UI: clean only UI node_modules, .next, and ui_dev.log
    if [[ "$CLEAN_UI" == true ]]; then
        local ui_dir="$SERVICES_DIR/report_service/ui"
        log "Cleaning UI dependencies in $ui_dir..."
        rm -rf "$ui_dir/node_modules" "$ui_dir/.next" "$ui_dir/ui_dev.log"
        log_success "UI cleaned."
    fi

    # CLEAN_FIRST (legacy/compatibility): clean everything except UI if no other clean flags
    if [[ "$CLEAN_FIRST" == true && "$CLEAN_ALL" != true && "$CLEAN_ANALYSIS" != true && "$CLEAN_REPORT" != true && "$CLEAN_UI" != true ]]; then
        log "Cleaning default components (legacy behavior)..."
        if lsof -Pi :$PYPISERVER_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_warning "Stopping PyPI server on port $PYPISERVER_PORT..."
            lsof -ti:$PYPISERVER_PORT | xargs kill -9 2>/dev/null || true
            sleep 1
        fi
        log_warning "Removing virtual environments..."
        rm -rf "$SHARED_LIB_VENV" "$ANALYSIS_VENV" "$REPORT_VENV" "$PYPISERVER_VENV"
        log_warning "Removing packages directory..."
        rm -rf "$PACKAGES_DIR"
        log_success "Cleanup complete (legacy)."
    fi
}

# Function: Setup PyPI server environment
setup_pypiserver() {
    log "Setting up PyPI server environment..."

    mkdir -p "$PYPISERVER_VENV" "$PACKAGES_DIR"

    if [ ! -f "$PYPISERVER_VENV/bin/activate" ]; then
        log "Creating PyPI server virtual environment..."
        python3 -m venv "$PYPISERVER_VENV"
        log_success "Virtual environment created"
    else
        log_success "PyPI server virtual environment already exists"
    fi

    # Install pypiserver
    log "Installing pypiserver and dependencies..."
    source "$PYPISERVER_VENV/bin/activate"
    pip install --quiet --upgrade pip setuptools wheel
    pip install --quiet pypiserver passlib
    deactivate

    log_success "PyPI server environment ready"
}

# Function: Build and deploy shared library
deploy_shared_lib() {
    log "Building and deploying shared_lib..."

    cd "$SERVICES_DIR/shared_lib"

    # Create shared lib venv
    if [ ! -f "$SHARED_LIB_VENV/bin/activate" ]; then
        log "Creating shared_lib virtual environment..."
        python3 -m venv "$SHARED_LIB_VENV" --prompt "social_pulse_common"
        log_success "Virtual environment created"
    fi

    source "$SHARED_LIB_VENV/bin/activate"

    # Install build dependencies
    log "Installing build dependencies..."
    pip install --quiet --upgrade pip setuptools wheel build
    pip install --quiet -r base-tooling-requirements.txt 2>/dev/null || log_warning "Some build dependencies could not be installed"

    # Clean previous builds
    rm -rf dist build src/*.egg-info 2>/dev/null || true

    # Build the wheel
    log "Building wheel package..."
    python3 -m build

    # Find wheel file
    WHEEL_FILE=$(find dist -name "socialpulse_common-*.whl" 2>/dev/null | head -1)
    if [ -z "$WHEEL_FILE" ]; then
        log_error "Could not find wheel file in dist/ directory"
        deactivate
        exit 1
    fi

    log_success "Wheel built: $(basename "$WHEEL_FILE")"

    # Copy to packages directory
    cp "$WHEEL_FILE" "$PACKAGES_DIR/"
    WHEEL_NAME=$(basename "$WHEEL_FILE")
    log_success "Deployed: $WHEEL_NAME"

    # Calculate hash
    PACKAGE_HASH=$(sha256sum "$PACKAGES_DIR/$WHEEL_NAME" | awk '{print $1}')
    echo "$PACKAGE_HASH" > "$PACKAGES_DIR/latest_hash.txt"

    deactivate

    # Update hash for socialpulse-common in requirements.txt for analysis_service and report_service using the shared_lib script
    for svc in analysis_service report_service; do
        svc_req="$SERVICES_DIR/$svc/requirements.txt"
        if [ -f "$svc_req" ]; then
            log "Updating hash for socialpulse-common in $svc_req using update_requirements_hash.sh..."
            whl_path="$PACKAGES_DIR/$WHEEL_NAME"
            new_hash=$(sha256sum "$WHEEL_FILE" | awk '{print $1}')
            "$SERVICES_DIR/shared_lib/scripts/update_requirements_hash.sh" "$new_hash" "$svc_req"
            log_success "Updated hash for socialpulse-common in $svc_req"
        fi
    done

    log_success "Shared library deployment complete"
}

# Function: Start PyPI server
start_pypiserver() {
    log "Starting PyPI server..."

    # Check if already running
    if lsof -Pi :$PYPISERVER_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_success "PyPI server already running on port $PYPISERVER_PORT"
        return
    fi

    source "$PYPISERVER_VENV/bin/activate"

    log "Launching pypi-server on port $PYPISERVER_PORT..."
    nohup pypi-server run -p "$PYPISERVER_PORT" -a . -P . "$PACKAGES_DIR" \
        > "$PACKAGES_DIR/pypiserver.log" 2>&1 &

    sleep 2

    deactivate

    if lsof -Pi :$PYPISERVER_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_success "PyPI server started on http://localhost:$PYPISERVER_PORT/simple"
    else
        log_error "PyPI server failed to start"
        log_error "Check logs at: $PACKAGES_DIR/pypiserver.log"
        exit 1
    fi
}

# Function: Prompt for database password
prompt_db_password() {
    if [ -z "$DB_PASSWORD" ]; then
        read -sp "Enter PostgreSQL password for '$DB_USER': " DB_PASSWORD
        echo
    fi
}

# Function: Test database connection
test_db_connection() {
    log "Testing PostgreSQL connection..."

    if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c "SELECT 1" >/dev/null 2>&1; then
        log_error "Failed to connect to PostgreSQL at $DB_HOST:$DB_PORT"
        log_error "Please ensure PostgreSQL is running and credentials are correct"
        exit 1
    fi

    log_success "PostgreSQL connection successful"
}

# Function: Create database
create_database() {
    local db_name=$1
    local db_user=$2

    log "Creating database: $db_name"

    # Check if database exists
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -tc "SELECT 1 FROM pg_database WHERE datname = '$db_name'" | grep -q 1; then
        log_warning "Database '$db_name' already exists, skipping creation"
        return
    fi

    # Create database
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" <<EOF
CREATE DATABASE $db_name;
GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;
\c $db_name
GRANT CREATE ON SCHEMA public TO $db_user;
GRANT USAGE ON SCHEMA public TO $db_user;
EOF

    log_success "Database created: $db_name"
}

# Function: Setup databases
setup_databases() {
    if [[ "$SKIP_DB" == true ]]; then
        log_warning "Skipping database setup"
        return
    fi

    log "Setting up PostgreSQL databases..."

    prompt_db_password
    test_db_connection

    create_database "social_pulse_db" "$DB_USER"
    create_database "social_pulse_reporting_db" "$DB_USER"

    log_success "Database setup complete"
}

# Function: Setup a service
setup_service() {
    local service_name=$1
    local service_path=$2
    local service_venv=$3
    local port=$4

    log "Setting up $service_name..."

    cd "$service_path"

    # Create virtual environment
    if [ ! -f "$service_venv/bin/activate" ]; then
        log "Creating $service_name virtual environment..."
        python3 -m venv "$service_venv" --prompt "social_pulse_$service_name"
        log_success "Virtual environment created"
    fi

    source "$service_venv/bin/activate"

    # Install dependencies
    log "Installing $service_name dependencies..."
    pip install --quiet --upgrade pip setuptools wheel
    pip install --quiet -r base-tooling-requirements.txt 2>/dev/null || log_warning "Some dependencies could not be installed"

    # Install from local PyPI with extra index URL
    log "Installing $service_name from local PyPI server..."
    if pip install --quiet \
        -r requirements.txt \
        --extra-index-url "http://localhost:$PYPISERVER_PORT/simple" \
        --trusted-host localhost 2>&1 | grep -i error; then
        log_warning "Some dependencies could not be installed from local PyPI"
    fi

    deactivate

    # Create .env file if it doesn't exist
    if [ ! -f "$service_path/.env" ]; then
        log "Creating .env file..."

        if [ -f "$service_path/.env.template" ]; then
            cp "$service_path/.env.template" "$service_path/.env"
            log_success ".env file created from template (update with your settings)"
        else
            cat > "$service_path/.env" <<EOF
# $service_name Configuration
APP_ENV=dev
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_USERNAME=$DB_USER
DB_PASSWORD=$DB_PASSWORD
EOF
            log_success ".env file created (update with your settings)"
        fi
    fi

    log_success "$service_name setup complete"
}

# Function: Setup services
setup_services() {
    if [[ "$SKIP_SERVICES" == true ]]; then
        log_warning "Skipping service setup"
        return
    fi

    log "Setting up services..."

    setup_service "analysis_service" \
        "$SERVICES_DIR/analysis_service" \
        "$ANALYSIS_VENV" \
        8080

    setup_service "report_service" \
        "$SERVICES_DIR/report_service" \
        "$REPORT_VENV" \
        8008

    log_success "Services setup complete"
}

# Function: Generate deployment summary
generate_summary() {
    cat > "$PROJECT_ROOT/.deployment_info.txt" <<EOF
Social Pulse Local Deployment Summary
=====================================
Deployment Date: $(date)

PyPI Server:
  URL: http://localhost:$PYPISERVER_PORT/simple
  Port: $PYPISERVER_PORT
  Packages: $PACKAGES_DIR
  Log: $PACKAGES_DIR/pypiserver.log

Shared Library:
  Location: $SERVICES_DIR/shared_lib
  Virtual Environment: $SHARED_LIB_VENV

Analysis Service:
  Location: $SERVICES_DIR/analysis_service
  Virtual Environment: $ANALYSIS_VENV
  Port: 8080 (when running)

Report Service:
  Location: $SERVICES_DIR/report_service
  Virtual Environment: $REPORT_VENV
  Port: 8008 (when running)

Database Configuration:
  Host: $DB_HOST
  Port: $DB_PORT
  User: $DB_USER
  Analysis DB: social_pulse_db
  Reporting DB: social_pulse_reporting_db

Next Steps:
1. Update .env files in each service with your configuration
2. Run database migrations (if needed)
3. Start the services using the provided helper scripts

Helper Scripts:
  Start all services: ./deploy/start_local_services.sh
  Stop all services: ./deploy/stop_local_services.sh
  View PyPI logs: tail -f $PACKAGES_DIR/pypiserver.log
EOF

    log_success "Deployment summary saved to .deployment_info.txt"
}

# Function: Deploy UI for report_service
deploy_ui() {
    local ui_dir="$SERVICES_DIR/report_service/ui"
    log "Deploying UI in $ui_dir..."
    if [ ! -d "$ui_dir" ]; then
        log_error "UI directory not found: $ui_dir"
        return 1
    fi
    cd "$ui_dir"
    log "Installing UI dependencies with npm ci..."
    npm ci || { log_error "npm ci failed"; return 1; }
    log_success "UI dependencies installed"
    log "Starting Next.js development server (npm run dev)..."
    nohup npm run dev > ui_dev.log 2>&1 &
    log_success "UI dev server started (http://localhost:9002)"
    cd "$PROJECT_ROOT"
}

# Function: Main execution
main() {
    parse_args "$@"

    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════╗"
    echo "║   Social Pulse - Local Deployment Script   ║"
    echo "╚════════════════════════════════════════════╝"
    echo -e "${NC}"

    check_prerequisites

    cleanup_previous

    setup_pypiserver
    deploy_shared_lib
    start_pypiserver

    if [[ "$SHARED_ONLY" != true ]]; then
        setup_databases
        setup_services
        deploy_ui
    fi

    generate_summary

    echo ""
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════╗"
    echo "║  ✓ Deployment Complete!                    ║"
    echo "╚════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo "PyPI Server: http://localhost:$PYPISERVER_PORT/simple"
    echo ""
    echo "Next steps:"
    echo "  1. Review and update .env files in each service"
    echo "  2. Run database migrations (if needed)"
    echo "  3. Start services: ./deploy/start_local_services.sh"
    echo "  4. View deployment info: cat .deployment_info.txt"
    echo ""
}

main "$@"
