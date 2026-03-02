# Social Pulse Deployment Scripts

This directory contains comprehensive scripts and documentation for deploying Social Pulse locally and to production (Google Cloud Platform).

## Quick Start

```bash
# 1. Deploy everything locally
./deploy_local.sh

# 2. Start services
./start_local_services.sh --background

# 3. Access services
# Analysis: http://localhost:8080/docs
# Report: http://localhost:8008/docs
# PyPI: http://localhost:3322/simple
```

## Scripts Overview

### `deploy_local.sh` - Main Deployment Script

Automates the complete local deployment including:
- Building the shared library package
- Setting up local PyPI server
- Creating PostgreSQL databases
- Installing dependencies for all services
- Configuring environments

**Usage:**
```bash
./deploy_local.sh [OPTIONS]

Options:
  --help              Show help
  --shared-only       Deploy only shared library
  --skip-db           Skip database setup
  --skip-services     Skip service setup
  --clean             Clean all except UI (legacy)
  --clean-all         Clean all components (shared lib, analysis, report, UI, PyPI, packages)
  --clean-analysis    Clean only the analysis service virtual environment
  --clean-report      Clean only the report service virtual environment
  --clean-ui          Clean only the UI (node_modules, .next, ui_dev.log)
  --clean-shared-lib  Clean only the shared library virtual environment
  --force-rebuild     Force rebuild
  --db-user USER      PostgreSQL user
  --db-password PASS  PostgreSQL password
  --db-host HOST      PostgreSQL host (default: localhost)
  --db-port PORT      PostgreSQL port (default: 5432)
  --pypi-port PORT    PyPI server port (default: 3322)
```

**Examples:**
```bash
# Full deployment
./deploy_local.sh

# Clean deployment (legacy)
./deploy_local.sh --clean

# Clean only UI
./deploy_local.sh --clean-ui

# Clean only shared lib venv
./deploy_local.sh --clean-shared-lib

# Deploy only shared library
./deploy_local.sh --shared-only

# Custom PostgreSQL credentials
./deploy_local.sh --db-user admin --db-password secret

# Custom PyPI port
./deploy_local.sh --pypi-port 3333
```

### `start_local_services.sh` - Start Services

Starts Social Pulse services (Analysis, Report, optionally UI).

**Usage:**
```bash
./start_local_services.sh [OPTIONS]

Options:
  --help              Show help
  --analysis-only     Start only analysis service
  --report-only       Start only report service
  --with-ui           Also start report UI
  --background        Run in background
```

**Examples:**
```bash
# Start all services in background
./start_local_services.sh --background

# Start analysis service in foreground
./start_local_services.sh --analysis-only

# Start with UI
./start_local_services.sh --with-ui --background
```

### `stop_local_services.sh` - Stop Services

Stops all running Social Pulse services.

**Usage:**
```bash
./stop_local_services.sh [OPTIONS]

Options:
  --help              Show help
  --full-cleanup      Stop services and clean up
  --kill-pypi         Also stop PyPI server
```

**Examples:**
```bash
# Stop all services
./stop_local_services.sh

# Stop and clean up
./stop_local_services.sh --full-cleanup

# Stop services and kill PyPI server
./stop_local_services.sh --kill-pypi
```

### `social_pulse.sh` - Quick Commands Wrapper

Convenient wrapper for common operations.

**Usage:**
```bash
./social_pulse.sh [COMMAND] [OPTIONS]

Commands:
  deploy       Full deployment
  start        Start all services
  stop         Stop all services
  status       Check service status
  logs         View service logs
  rebuild      Rebuild shared library
  migrate      Run database migrations
  clean        Full cleanup
  help         Show help
```

**Examples:**
```bash
# Deploy
./social_pulse.sh deploy

# Start with UI
./social_pulse.sh start --with-ui --background

# Check status
./social_pulse.sh status

# View logs
./social_pulse.sh logs --follow

# Run migrations
./social_pulse.sh migrate
```

## Documentation

### `DEPLOYMENT_GUIDE.md`

Comprehensive guide covering:
- Prerequisites and installation
- Detailed step-by-step setup
- Service management
- Configuration
- Development workflows
- Advanced topics

**Read it for:**
- First-time setup
- Configuration details
- Development workflows
- Advanced usage

### `TROUBLESHOOTING.md`

Solutions for common issues:
- PostgreSQL connection problems
- PyPI server issues
- Port conflicts
- Database migrations
- Environment configuration
- Complete reset procedures

**Read it for:**
- Error resolution
- Debugging tips
- System resource checks
- Getting help

## Directory Structure

```
deploy/
├── deploy_local.sh              # Main deployment script
├── start_local_services.sh      # Start services
├── stop_local_services.sh       # Stop services
├── social_pulse.sh              # Quick commands wrapper
├── deploy.sh                    # GCP deployment (existing)
├── DEPLOYMENT_GUIDE.md          # Complete deployment guide
├── TROUBLESHOOTING.md           # Troubleshooting guide
├── README.md                    # This file
├── Dockerfile                   # Container definition
├── cloudbuild.yaml             # Google Cloud Build config
├── terraform/                  # GCP infrastructure as code
└── containers/                 # Container build context
```

## Typical Workflow

### First-Time Setup

```bash
# 1. Navigate to project root
cd /path/to/social_pulse

# 2. Run deployment
./deploy/deploy_local.sh

# 3. When prompted, enter PostgreSQL password

# 4. Start services in background
./deploy/start_local_services.sh --background

# 5. Verify services are running
./deploy/social_pulse.sh status
```

### Daily Development

```bash
# Start services
./deploy/start_local_services.sh --background

# Make code changes

# Stop services when done
./deploy/stop_local_services.sh

# Or view logs while developing
tail -f .analysis_service.log
```

### After Modifying Shared Library

```bash
# Rebuild and redeploy shared library
./deploy/deploy_local.sh --force-rebuild --shared-only

# Update dependent services
cd services/analysis_service
pip install --force-reinstall -r requirements.txt \
  --extra-index-url http://localhost:3322/simple \
  --trusted-host localhost
```

## Environment Setup

### Prerequisites

- **Python 3.12+**
- **PostgreSQL 12+**
- **pip 24.3+**
- **Node.js 18+** (optional, for UI)

### Verify Setup

```bash
python3 --version    # Should be 3.12+
pip3 --version       # Should be 24.3+
psql --version       # Should be 12+
```

## Service Ports

Default ports used by Social Pulse:

| Service | Port | URL |
|---------|------|-----|
| Analysis Service | 8080 | http://localhost:8080 |
| Report Service | 8008 | http://localhost:8008 |
| Report UI | 3000 | http://localhost:3000 |
| PyPI Server | 3322 | http://localhost:3322 |

## Database Configuration

Two PostgreSQL databases are created:

| Database | User | Purpose |
|----------|------|---------|
| social_pulse_db | social_pulse_user | Analysis Service |
| social_pulse_reporting_db | social_pulse_user | Report Service |

## Useful Commands

### Check Service Status

```bash
./social_pulse.sh status
```

### View Logs

```bash
# Follow all logs
./social_pulse.sh logs --follow

# Specific service logs
tail -f .analysis_service.log
tail -f .report_service.log
tail -f ~/.social_pulse/packages/pypiserver.log
```

### Rebuild Shared Library

```bash
./deploy_local.sh --force-rebuild --shared-only
```

### Reset Everything

```bash
./deploy/stop_local_services.sh --full-cleanup
./deploy/deploy_local.sh --clean
```

### Start Services with Debugging

```bash
# Terminal 1: Analysis Service
cd services/analysis_service/src
source ../.venv/bin/activate
APP_ENV=dev uvicorn api.runner_entry:app --reload --port 8080

# Terminal 2: Report Service
cd services/report_service/src
source ../.venv/bin/activate
APP_ENV=dev uvicorn main:app --reload --port 8008
```

## Troubleshooting

### Quick Diagnostics

```bash
# Check Python and dependencies
python3 --version
pip3 --version

# Verify PostgreSQL
psql -U postgres -d postgres -c "SELECT 1"

# Check ports
lsof -i :8080
lsof -i :8008
lsof -i :3322

# View deployment info
cat .deployment_info.txt
```

### Common Issues

**PostgreSQL connection failed:**
```bash
brew services start postgresql  # macOS
```

**Port already in use:**
```bash
lsof -ti:3322 | xargs kill -9
```

**PyPI server not working:**
```bash
curl http://localhost:3322/simple/
tail -f ~/.social_pulse/packages/pypiserver.log
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

## GCP Deployment

For production deployment to Google Cloud:

1. **Configure credentials:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Update terraform variables:**
   ```bash
   cd terraform
   nano terraform.tfvars
   ```

3. **Deploy to GCP:**
   ```bash
   cd deploy
   ./deploy.sh YOUR_PROJECT_ID
   ```

See `terraform/` directory for infrastructure-as-code configuration.

## Support

- **Documentation:** See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Troubleshooting:** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Main Project:** See [../README.md](../README.md)
- **Services:** See individual service READMEs in `services/`

## Scripts Maintenance

To update scripts:

1. Modify the `.sh` file
2. Test the changes locally
3. Commit to version control
4. Document changes in this README

## License

These deployment scripts are part of Social Pulse and follow the same license as the main project.

---

**Last Updated:** 2025-02-17

For more information, see the [Deployment Guide](DEPLOYMENT_GUIDE.md).
