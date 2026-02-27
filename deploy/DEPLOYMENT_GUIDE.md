# Social Pulse Local Deployment Guide

This guide provides step-by-step instructions for deploying and running the complete Social Pulse application locally.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Managing Services](#managing-services)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [Development Workflow](#development-workflow)

## Prerequisites

Before starting the deployment, ensure you have:

### Required Software

- **Python 3.12+** - [Install Python](https://www.python.org/downloads/)
- **pip 24.3+** - Usually comes with Python
- **PostgreSQL 12+** - [Install PostgreSQL](https://www.postgresql.org/download/)
- **Git** - For version control

### Optional

- **Node.js 18+** - Only if you want to run the Report UI
- **npm/yarn** - For managing JavaScript dependencies

### Verify Installation

```bash
python3 --version      # Should be 3.12 or higher
pip3 --version         # Should be 24.3 or higher
psql --version         # Should be 12 or higher
```

## Quick Start

The fastest way to get Social Pulse running locally:

```bash
# 1. Navigate to the project root
cd /path/to/social_pulse

# 2. Make deployment scripts executable
chmod +x deploy/deploy_local.sh
chmod +x deploy/start_local_services.sh
chmod +x deploy/stop_local_services.sh

# 3. Run the deployment script
# When prompted, enter your PostgreSQL password
./deploy/deploy_local.sh

# 4. Start the services
./deploy/start_local_services.sh --background

# 5. Access the services
# Analysis Service: http://localhost:8080/docs
# Report Service: http://localhost:8008/docs
# PyPI Server: http://localhost:3322/simple
```

## Detailed Setup

### Step 1: Verify Prerequisites

```bash
# Check Python version
python3 --version

# Check pip version
pip3 --version

# Verify PostgreSQL is installed and running
psql --version

# Test PostgreSQL connection
psql -U postgres -d postgres -c "SELECT 1"
```

### Step 2: Make Scripts Executable

```bash
chmod +x deploy/deploy_local.sh
chmod +x deploy/start_local_services.sh
chmod +x deploy/stop_local_services.sh
```

### Step 3: Run Deployment Script

The deployment script automates the complete setup process:

```bash
./deploy/deploy_local.sh
```

When prompted, enter your PostgreSQL credentials (the script will prompt for a password).

#### Deployment Script Options

```bash
# Basic deployment
./deploy/deploy_local.sh

# Deploy only shared library
./deploy/deploy_local.sh --shared-only

# Skip database creation
./deploy/deploy_local.sh --skip-db

# Clean previous deployment first
./deploy/deploy_local.sh --clean

# Force rebuild even if already deployed
./deploy/deploy_local.sh --force-rebuild

# Custom PostgreSQL credentials
./deploy/deploy_local.sh \
  --db-user my_user \
  --db-password my_password \
  --db-host localhost \
  --db-port 5432

# Custom PyPI server port
./deploy/deploy_local.sh --pypi-port 3333
```

### Step 4: Configure Services

Each service requires environment configuration. After deployment, update the `.env` files:

#### Analysis Service Configuration

```bash
cd services/analysis_service
nano .env  # or use your preferred editor
```

Example `.env`:
```
APP_ENV=dev
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=social_pulse_user
DB_PASSWORD=your_password
DB_NAME=social_pulse_db
```

#### Report Service Configuration

```bash
cd services/report_service
nano .env
```

Example `.env`:
```
APP_ENV=dev
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=social_pulse_user
DB_PASSWORD=your_password
DB_NAME=social_pulse_reporting_db
```

### Step 5: Run Database Migrations

Each service needs to initialize its database schema:

#### Analysis Service Migrations

```bash
cd services/analysis_service
source .venv/bin/activate

# Initialize yoyo migrations
yoyo init \
  --database postgresql://social_pulse_user:password@localhost:5432/social_pulse_db \
  db-migrations/

# Apply migrations
yoyo apply
```

#### Report Service Migrations

```bash
cd services/report_service
source .venv/bin/activate

# Initialize yoyo migrations
yoyo init \
  --database postgresql://social_pulse_user:password@localhost:5432/social_pulse_reporting_db \
  db-migrations/

# Apply migrations
yoyo apply
```

## Managing Services

### Starting Services

#### Start All Services in Background

```bash
./deploy/start_local_services.sh --background
```

#### Start Analysis Service Only

```bash
./deploy/start_local_services.sh --analysis-only
```

#### Start Report Service Only

```bash
./deploy/start_local_services.sh --report-only
```

#### Start with Report UI

```bash
./deploy/start_local_services.sh --with-ui --background
```

#### Start in Foreground (for debugging)

```bash
./deploy/start_local_services.sh
# Press Ctrl+C to stop
```

### Stopping Services

#### Stop All Services

```bash
./deploy/stop_local_services.sh
```

#### Stop with Full Cleanup

```bash
./deploy/stop_local_services.sh --full-cleanup
```

#### Stop PyPI Server

```bash
./deploy/stop_local_services.sh --kill-pypi
```

### Checking Service Status

```bash
# Check Analysis Service
curl http://localhost:8080/docs

# Check Report Service
curl http://localhost:8008/docs

# Check PyPI Server
curl http://localhost:3322/simple/socialpulse-common/
```

### Viewing Logs

```bash
# Analysis Service logs
tail -f .analysis_service.log

# Report Service logs
tail -f .report_service.log

# PyPI Server logs
tail -f ~/.social_pulse/packages/pypiserver.log

# Report UI logs
tail -f .report_ui.log
```

## Configuration

### Service Ports

By default, services run on:
- **Analysis Service**: `http://localhost:8080`
- **Report Service**: `http://localhost:8008`
- **Report UI**: `http://localhost:3000` (if enabled)
- **PyPI Server**: `http://localhost:3322`

To change ports, modify the scripts or start services manually:

```bash
cd services/analysis_service/src
source ../.venv/bin/activate
APP_ENV=dev uvicorn api.runner_entry:app --reload --port=8090
```

### Database Configuration

The deployment script creates two databases:
- `social_pulse_db` - Analysis Service database
- `social_pulse_reporting_db` - Report Service database

Both use the same PostgreSQL user by default. To use different users:

```bash
./deploy/deploy_local.sh --db-user social_pulse_user
```

### PyPI Server Configuration

The local PyPI server is hosted on port 3322 by default. To use a different port:

```bash
./deploy/deploy_local.sh --pypi-port 3333
```

## Troubleshooting

### Issue: "PostgreSQL connection failed"

**Solution**: Ensure PostgreSQL is running and credentials are correct:

```bash
# Start PostgreSQL (macOS)
brew services start postgresql

# Test connection
psql -h localhost -U postgres -d postgres -c "SELECT 1"
```

### Issue: "PyPI server failed to start"

**Solution**: Check if port 3322 is already in use:

```bash
# Check what's using port 3322
lsof -i :3322

# Kill the process if needed
kill -9 <PID>

# Try deployment again
./deploy/deploy_local.sh
```

### Issue: "Port 8080 already in use"

**Solution**: Either stop the service using that port or start on a different port:

```bash
# Find and stop process
lsof -i :8080
kill -9 <PID>

# Or start on different port
cd services/analysis_service/src
uvicorn api.runner_entry:app --reload --port=8090
```

### Issue: "pip install fails with module not found"

**Solution**: Ensure the PyPI server is running before installing dependencies:

```bash
# Check if PyPI server is running
curl http://localhost:3322/simple/

# If not, start it
./deploy/deploy_local.sh
```

### Issue: "Database migration fails"

**Solution**: Verify the database exists and user has permissions:

```bash
# Connect to database
psql -U social_pulse_user -d social_pulse_db -h localhost

# Check tables
\dt

# Exit
\q
```

### Issue: ".env file not found"

**Solution**: Create it from template or generate a new one:

```bash
cd services/analysis_service
cp .env.template .env
# Edit with your settings
```

## Development Workflow

### Making Changes to Shared Library

When you modify the shared library:

1. **Make your changes** in `services/shared_lib/src/`

2. **Rebuild and redeploy**:
   ```bash
   ./deploy/deploy_local.sh --force-rebuild
   ```

3. **Update dependent services**:
   ```bash
   cd services/analysis_service
   source .venv/bin/activate
   pip install --force-reinstall \
     --no-deps \
     -r requirements.txt \
     --extra-index-url http://localhost:3322/simple \
     --trusted-host localhost
   ```

### Making Changes to Services

When you modify service code:

1. **Stop the service**:
   ```bash
   ./deploy/stop_local_services.sh
   ```

2. **Make your changes** in `services/analysis_service/src/` or `services/report_service/src/`

3. **Services will auto-reload** with `--reload` flag, or restart them:
   ```bash
   ./deploy/start_local_services.sh --background
   ```

### Running Tests

```bash
# Test shared library
cd services/shared_lib
source .venv/bin/activate
pytest tests/

# Test analysis service
cd services/analysis_service
source .venv/bin/activate
pytest tests/

# Test report service
cd services/report_service
source .venv/bin/activate
pytest tests/
```

### Updating Dependencies

When adding new dependencies:

1. **Update `requirements.in`**:
   ```bash
   cd services/analysis_service
   nano requirements.in  # Add new dependency
   ```

2. **Compile new requirements**:
   ```bash
   pip-compile \
     --generate-hashes \
     --extra-index-url http://localhost:3322/simple \
     --trusted-host localhost \
     --no-emit-index-url \
     requirements.in
   ```

3. **Install updated requirements**:
   ```bash
   pip install -r requirements.txt
   ```

## Advanced Topics

### Running Multiple Instances

You can run multiple instances of services on different ports:

```bash
# Terminal 1: Start Analysis Service on 8080
cd services/analysis_service/src
source ../.venv/bin/activate
APP_ENV=dev uvicorn api.runner_entry:app --reload --port=8080

# Terminal 2: Start Analysis Service on 8081
cd services/analysis_service/src
source ../.venv/bin/activate
APP_ENV=dev uvicorn api.runner_entry:app --reload --port=8081

# Terminal 3: Start Report Service on 8008
cd services/report_service/src
source ../.venv/bin/activate
APP_ENV=dev uvicorn main:app --reload --port=8008
```

### Using Docker (Optional)

For isolated development environments, consider using Docker:

```bash
# Build Docker image
docker build -t social-pulse .

# Run containers
docker-compose up
```

### Debugging with IDE

To debug with VS Code or PyCharm:

1. Install the debugger:
   ```bash
   source .venv/bin/activate
   pip install debugpy
   ```

2. Configure your IDE to attach to port 5678

3. Start service with debugger:
   ```bash
   python -m debugpy --listen 5678 -m uvicorn api.runner_entry:app --reload
   ```

## Support and Documentation

- [Social Pulse README](../README.md)
- [Shared Library README](../services/shared_lib/README.md)
- [Analysis Service README](../services/analysis_service/README.md)
- [Report Service README](../services/report_service/README.md)
- [Deployment Scripts](.)

## Common Commands Reference

```bash
# Full deployment
./deploy/deploy_local.sh

# Start all services
./deploy/start_local_services.sh --background

# Stop all services
./deploy/stop_local_services.sh

# View deployment info
cat .deployment_info.txt

# Rebuild shared library
./deploy/deploy_local.sh --force-rebuild --shared-only

# Check service status
curl http://localhost:8080/docs
curl http://localhost:8008/docs

# View logs
tail -f ~/.social_pulse/packages/pypiserver.log

# Clean everything
./deploy/stop_local_services.sh --full-cleanup
./deploy/deploy_local.sh --clean
```

---

For more information and troubleshooting, see the main [README.md](../README.md) and service-specific documentation.

## Cleaning Components

You can selectively clean components before deployment using these flags:

- `--clean-all`         Clean all components (shared lib, analysis, report, UI, PyPI, packages)
- `--clean-analysis`    Clean only the analysis service virtual environment
- `--clean-report`      Clean only the report service virtual environment
- `--clean-ui`          Clean only the UI (node_modules, .next, ui_dev.log)
- `--clean-shared-lib`  Clean only the shared library virtual environment
- `--clean`             Clean all except UI (legacy)

Example:
```bash
./deploy/deploy_local.sh --clean-report
./deploy/deploy_local.sh --clean-all
./deploy/deploy_local.sh --clean-ui
./deploy/deploy_local.sh --clean-shared-lib
```

## Script Options Reference

### deploy_local.sh

```bash
./deploy/deploy_local.sh [OPTIONS]

Options:
  --help              Show this help message
  --shared-only       Deploy only the shared library
  --skip-db           Skip database creation
  --skip-services     Skip service setup
  --clean             Clean up all artifacts and databases before deployment (legacy: cleans all except UI)
  --clean-all         Clean all components (shared lib, analysis, report, UI, PyPI, packages)
  --clean-analysis    Clean only the analysis service virtual environment
  --clean-report      Clean only the report service virtual environment
  --clean-ui          Clean only the UI (node_modules, .next, ui_dev.log)
  --clean-shared-lib  Clean only the shared library virtual environment
  --force-rebuild     Force rebuild even if already deployed
  --db-user USER      PostgreSQL user (default: social_pulse_user)
  --db-password PASS  PostgreSQL password (default: prompted)
  --db-host HOST      PostgreSQL host (default: localhost)
  --db-port PORT      PostgreSQL port (default: 5432)
  --pypi-port PORT    Local PyPI server port (default: 3322)
```
