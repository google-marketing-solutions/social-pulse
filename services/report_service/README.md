# Social Pulse - Reporting Service

The Reporting Service manages report creation, persistence configurations, and exposes the user-facing API.

## Local Development Workflow

### 1. Environment Setup

First, create a virtual environment and install the dependencies.

```bash
# Create and activate virtual environment
python3 -m venv .venv --prompt "social_pulse_reporting"
source .venv/bin/activate

# Install development dependencies
pip install -r base-tooling-requirements.txt

# Install project dependencies
# Note: Ensure the local PyPI server is running (see shared_lib/README.md)
pip install \
    -r requirements.txt \
    --extra-index-url http://localhost:3322/simple \
    --trusted-host localhost
```

### 2. Configuration

Copy the template environment file and update it with your local configuration.

```bash
cp .env.template .env
# Edit .env and set your database credentials and API keys
```

### 3. Database Setup

Set up the PostgreSQL database for the Reporting Service.

1.  **Create Database and User**:
    ```bash
    sudo -i -u postgres psql
    ```
    ```sql
    CREATE DATABASE social_pulse_reporting_db;
    CREATE USER social_pulse_reporting_user WITH PASSWORD '[Your Password]';
    GRANT ALL PRIVILEGES ON DATABASE social_pulse_reporting_db to social_pulse_reporting_user;
    \c social_pulse_reporting_db
    GRANT CREATE ON SCHEMA public TO social_pulse_reporting_user;
    GRANT USAGE ON SCHEMA public TO social_pulse_reporting_user;
    \q
    ```

2.  **Verify Access**:
    ```bash
    psql -U social_pulse_reporting_user -d social_pulse_reporting_db -h localhost -W
    ```
    ```sql
    SELECT has_database_privilege('social_pulse_reporting_user', 'social_pulse_reporting_db', 'CONNECT');
    SELECT has_schema_privilege('social_pulse_reporting_user', 'public', 'CREATE');
    ```

3.  **Run Migrations**:
    Initialize and run Yoyo migrations to set up the schema.
    ```bash
    # Initialize yoyo config
    yoyo init \
      --database postgresql://social_pulse_reporting_user:[Your Password]@localhost:5432/social_pulse_reporting_db \
      db-migrations/

    # Apply migrations
    yoyo apply
    ```

### 4. Running the Service

You can run the Reporting API using `uvicorn` (typically exposed on port 8008).

```bash
# From the services/report_service directory
cd src/
APP_ENV=dev uvicorn main:app --reload --port=8008
```

### 5. Running Tests

This service uses `pytest` for unit testing.

```bash
pytest tests/
```

### 6. Dependency Management

We use `pip-compile` to manage `requirements.txt` with hash checking.

If you need to add or update a dependency:
1.  Edit `requirements.in`.
2.  Compile the new requirements:
    ```bash
    pip-compile \
       --generate-hashes \
       --extra-index-url http://localhost:3322/simple \
       --trusted-host localhost \
       --no-emit-index-url \
       requirements.in
    ```

## Usage

### Create a Report

You can create a new report by sending a POST request to the API:

```bash
curl -X POST http://localhost:8008/api/report \
  -v \
  -H "Content-Type: application/json" \
  -d '{
    "sources": [
      "YOUTUBE_VIDEO",
      "YOUTUBE_COMMENT"
    ],
    "data_output": "SENTIMENT_SCORE",
    "topic": "Acme Widgets",
    "start_time": "2025-10-01T00:00:00Z",
    "end_time": "2025-10-06T12:00:00Z",
    "include_justifications": true
  }'
```