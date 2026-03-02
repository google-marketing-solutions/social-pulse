# Gemini Social Sentiment Analyzer - Analysis Service

The Analysis Service is responsible for coordinating the sentiment analysis workflow, breaking down reports into individual tasks and executing them.

## Local Development Workflow

### 1. Environment Setup

First, create a virtual environment and install the dependencies.

```bash
# Create and activate virtual environment
cd services/analysis_service
python3 -m venv .venv --prompt "social_pulse_analysis"
source .venv/bin/activate

# Install development dependencies
pip install -r base-tooling-requirements.txt

# Install project dependencies
# Note: Ensure the local PyPI server is running (see shared_lib/README.md)
pip install \
    -r requirements.txt \
    --force-reinstall \
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

Set up the PostgreSQL database for the Analysis Service.

1.  **Create Database and User**:
    ```bash
    sudo -i -u postgres psql
    ```
    ```sql
    CREATE DATABASE social_pulse_db;
    CREATE USER social_pulse_user WITH PASSWORD '[Your Password]';
    GRANT ALL PRIVILEGES ON DATABASE social_pulse_db to social_pulse_user;
    \c social_pulse_db
    GRANT CREATE ON SCHEMA public TO social_pulse_user;
    GRANT USAGE ON SCHEMA public TO social_pulse_user;
    \q
    ```

2.  **Verify Access**:
    ```bash
    psql -U social_pulse_user -d social_pulse_db -h localhost -W
    ```
    ```sql
    SELECT has_database_privilege('social_pulse_user', 'social_pulse_db', 'CONNECT');
    SELECT has_schema_privilege('social_pulse_user', 'public', 'CREATE');
    ```

3.  **Run Migrations**:
    Initialize and run Yoyo migrations to set up the schema.
    ```bash
    # Initialize yoyo config
    yoyo init \
      --database postgresql://social_pulse_user:[Your Password]@localhost:5432/social_pulse_db \
      db-migrations/

    # Apply migrations
    yoyo apply
    ```

### 4. Running the Service

You can run the Analysis Service API using `uvicorn`.

```bash
cd src
APP_ENV=dev uvicorn api.runner_entry:app --reload --port=8080
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
