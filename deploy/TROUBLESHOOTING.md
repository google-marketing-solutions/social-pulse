# Social Pulse Local Deployment - Troubleshooting Guide

## Common Issues and Solutions
P.S: Run the commands in the *Solutions* sections from the root of the social_pulse repository

### 1. PostgreSQL Connection Issues

#### Error: "connection refused" or "could not connect to server"

**Causes:**
- PostgreSQL is not installed
- PostgreSQL service is not running
- Wrong credentials provided
- PostgreSQL not listening on localhost

**Solutions:**

```bash
# Check if PostgreSQL is installed
psql --version

# macOS: Start PostgreSQL using Homebrew
brew services start postgresql

# Linux: Start PostgreSQL service
sudo systemctl start postgresql

# Verify PostgreSQL is running
pg_isready -h localhost

# Test basic connection
psql -h localhost -U postgres -d postgres -c "SELECT 1"

# If you get authentication error, reset password
# macOS: Stop and restart with password reset
brew services stop postgresql
rm /usr/local/var/postgres/postmaster.pid
brew services start postgresql
```

#### Error: "permission denied" or "role does not exist"

**Solutions:**

```bash
# Connect as postgres superuser
psql -U postgres

# Inside psql, create the user:
CREATE USER social_pulse_user WITH PASSWORD 'your_password';

# Grant privileges
GRANT CREATEDB ON DATABASE postgres TO social_pulse_user;

# Exit psql
\q
```

### 2. PyPI Server Issues

#### Error: "PyPI server failed to start" or "Address already in use"

**Check what's using the port:**

```bash
# Find process using port 3322
lsof -i :3322

# Kill the process
kill -9 <PID>

# Wait a moment and try deployment again
sleep 2
./deploy/deploy_local.sh
```

#### Error: "Package not found" when installing services

**Solutions:**

```bash
# Check if PyPI server is running
curl http://localhost:3322/simple/

# View PyPI server logs
tail -f ~/.social_pulse/packages/pypiserver.log

# If not running, start deployment again
./deploy/deploy_local.sh

# Manually start PyPI server
source ~/.social_pulse/venv/pypiserver/bin/activate
pypi-server run -p 3322 ~/.social_pulse/packages
```

### 3. Python Virtual Environment Issues

#### Error: "source: no such file or directory" or ".venv not found"

**Solutions:**

```bash
# Recreate virtual environment
rm -rf services/shared_lib/.venv
./deploy/deploy_local.sh

# Or for specific service
rm -rf services/analysis_service/.venv
./deploy/deploy_local.sh
```

#### Error: "ModuleNotFoundError" or "No module named..."

**Solutions:**

```bash
# Reinstall dependencies
cd services/analysis_service
source .venv/bin/activate
pip install --force-reinstall \
  -r requirements.txt \
  --extra-index-url http://localhost:3322/simple \
  --trusted-host localhost

# Or for shared library
cd services/shared_lib
source .venv/bin/activate
pip install -r base-tooling-requirements.txt
```

### 4. Service Port Issues

#### Error: "Address already in use" on port 8080 or 8008

**Find and stop conflicting services:**

```bash
# Find process using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or stop all services
./deploy/stop_local_services.sh

# Start on different port
cd services/analysis_service/src
uvicorn api.runner_entry:app --reload --port 8090
```

#### Error: "Cannot bind to port" or permission denied

**Solution:** Use a port above 1024:

```bash
# For Analysis Service
cd services/analysis_service/src
uvicorn api.runner_entry:app --reload --port 8090

# For Report Service
cd services/report_service/src
uvicorn main:app --reload --port 8009
```

### 5. Database Migration Issues

#### Error: "No such table" or database schema not created

**Solutions:**

```bash
# Check if migrations exist
ls services/analysis_service/db-migrations/

# Run migrations manually
cd services/analysis_service
source .venv/bin/activate
yoyo apply --database postgresql://user:password@localhost:5432/social_pulse_db db-migrations/

# If yoyo is not installed
pip install yoyo-migrations
```

#### Error: "permission denied" during migration

**Solutions:**

```bash
# Grant schema permissions
psql -h localhost -U social_pulse_user -d social_pulse_db <<EOF
GRANT ALL ON SCHEMA public TO social_pulse_user;
GRANT CREATE ON SCHEMA public TO social_pulse_user;
EOF
```

### 6. Dependency and Build Issues

#### Error: "pip install fails" or "wheel building failed"

**Solutions:**

```bash
# Upgrade pip, setuptools, wheel
python3 -m pip install --upgrade pip setuptools wheel

# Clear pip cache
pip cache purge

# Try installation again with verbose output
pip install -r requirements.txt -v

# For build failures, install build dependencies
pip install build setuptools setuptools-scm
```

#### Error: "no module named 'google'" or GCP libraries not found

**Solutions:**

```bash
cd services/shared_lib
source .venv/bin/activate
pip install google-cloud-bigquery google-api-python-client
```

### 7. Environment Configuration Issues

#### Error: ".env file not found" or configuration error

**Solutions:**

```bash
# Create .env file from template
cd services/analysis_service
cp .env.template .env

# Edit with your settings
nano .env

# Make sure to include:
# - APP_ENV=dev
# - DB_HOST=localhost
# - DB_PASSWORD=your_password
# - etc.

# Verify file exists and is readable
cat .env
```

#### Error: "Cannot read configuration" or undefined variable

**Solutions:**

```bash
# Check .env file syntax
cat services/analysis_service/.env

# Ensure all required variables are set
# Required for Analysis Service:
# - APP_ENV
# - DB_HOST
# - DB_PORT
# - DB_USERNAME
# - DB_PASSWORD
# - DB_NAME

# Reload environment
source services/analysis_service/.env
```

### 8. Script Execution Issues

#### Error: "Permission denied" when running scripts

**Solutions:**

```bash
# Make scripts executable
chmod +x deploy/deploy_local.sh
chmod +x deploy/start_local_services.sh
chmod +x deploy/stop_local_services.sh
chmod +x deploy/social_pulse.sh

# Verify they're executable
ls -la deploy/*.sh
```

#### Error: "Command not found" or script not found

**Solutions:**

```bash
# Use full path or relative path
./deploy/deploy_local.sh

# Or cd first
cd deploy
./deploy_local.sh

# Not:
deploy/deploy_local.sh  # Without ./
```

### 9. Network and Connection Issues

#### Error: "Connection refused" when accessing services

**Verify services are running:**

```bash
# Check service ports
lsof -i :8080
lsof -i :8008
lsof -i :3322

# If nothing listed, services are not running
./deploy/start_local_services.sh --background

# Check service logs
tail -f .analysis_service.log
```

#### Error: "Name or service not known" or host not found

**Solutions:**

```bash
# Use localhost or 127.0.0.1
curl http://localhost:8080/docs

# Not:
curl http://social-pulse:8080/docs  # This won't work locally

# Check network connectivity
ping localhost
curl -v http://localhost:3322/simple/
```

### 10. Cleanup and Reset

#### Total Reset of Deployment

If everything is broken, do a complete reset:

```bash
# 1. Stop all services
./deploy/stop_local_services.sh --full-cleanup

# 2. Kill any remaining processes
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
lsof -ti:8008 | xargs kill -9 2>/dev/null || true
lsof -ti:3322 | xargs kill -9 2>/dev/null || true

# 3. Remove all environments
rm -rf services/shared_lib/.venv
rm -rf services/analysis_service/.venv
rm -rf services/report_service/.venv
rm -rf ~/.social_pulse

# 4. Remove generated files
rm -f .analysis_service.log
rm -f .report_service.log
rm -f .deployment_info.txt

# 5. Start fresh
./deploy/deploy_local.sh
```

## Cleaning and Resetting

If you need to clean specific components before redeployment, use:

- `--clean-all`         Clean all components (shared lib, analysis, report, UI, PyPI, packages)
- `--clean-analysis`    Clean only the analysis service virtual environment
- `--clean-report`      Clean only the report service virtual environment
- `--clean-ui`          Clean only the UI (node_modules, .next, ui_dev.log)
- `--clean-shared-lib`  Clean only the shared library virtual environment
- `--clean`             Clean all except UI (legacy)

Example:
```bash
./deploy/deploy_local.sh --clean-ui
./deploy/deploy_local.sh --clean-all
```

## Getting Help

If you're still having issues:

1. **Check logs:**
   ```bash
   tail -f ~/.social_pulse/packages/pypiserver.log
   tail -f .analysis_service.log
   tail -f .report_service.log
   ```

2. **Run in debug mode:**
   ```bash
   bash -x ./deploy/deploy_local.sh 2>&1 | tee deployment.log
   ```

3. **Review the deployment guide:**
   ```bash
   cat DEPLOYMENT_GUIDE.md
   ```

4. **Check system resources:**
   ```bash
   # Check available disk space
   df -h

   # Check memory
   free -h  # Linux
   vm_stat  # macOS

   # Check running processes
   ps aux | grep -E "python|postgres|pypi"
   ```

## Contact and Support

For more help:
- Review the main [README.md](../README.md)
- Check service-specific READMEs
- Review deployment scripts for inline comments
- Check Python/PostgreSQL documentation
