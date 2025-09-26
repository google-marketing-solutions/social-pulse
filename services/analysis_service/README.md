## Local Developement

### Setting up environment

1. Using a Google Cloud Project, create a Big Query dataset called
   "social_pulse_sentiment_data" and make sure you pick the specific location
   of "us-central1" to host it.  This is required so that the Gemini models can
   be found by Big Query.

2. Create a virtual environmnet for the microservice.

3. Install the required packages.
   ```
   pip install \
      -r requirements.txt \
      -r requirements-dev.txt \
      -find-links=../shared_lib/dist
   ```

4. Copy the ".env.template" file to a .env file and provide the values as
   needed.


### Setting up application PostgresDB

1. Install PostgresDB on your local system.

2. Create Social Pulse app database and user.
   ```
   sudo -i -u postgres
   psql

   CREATE DATABASE social_pulse_db;
   CREATE USER social_pulse_user WITH PASSWORD '[Your DB passowrd]';
   GRANT ALL PRIVILEGES ON DATABASE social_pulse_db to social_pulse_user;
   \q
   ```

3. Log into the Social Pulse app DB and set up schema access
   ```
   psql -d social_pulse_db

   GRANT CREATE ON SCHEMA public TO social_pulse_user;
   GRANT USAGE ON SCHEMA public TO social_pulse_user;
   ```

4. Test connecting to the Social Pulse app DB as the user,
   and verify that the user has the proper access (the
   queries below should both return 't' for TRUE.
   ```
   exit
   psql -U social_pulse_user -d social_pulse_db -h localhost -W

   SELECT has_database_privilege('social_pulse_user', 'social_pulse_reporting', 'CONNECT');
   SELECT has_schema_privilege('social_pulse_user', 'public', 'CREATE');
   ```

5. Init Yoyo so it can create a `yoyo.ini` file for you to use when running
   your migrations.
   ```
   yoyo init \
      --database postgresql://social_pulse_user:[Your DB password]@localhost:5432/social_pulse_db \
      db-migrations/
   ```

6. Run Yoyo migrations to set up the Social Pulse app DB.
   ```
   yoyo apply
   ```

### Running the unit tests

Pytest is used to run the unit tests, so you can run `pytest` in the appropriate
service directory.  For example:

```
cd services/analysis_service
pytest /tests

```

### Running the Report Runner API
Once everything has been set up, you can run the Report Runner API using the
uvicorn command.

```
cd services/analysis_service/src
uvicorn api.runner_entry:app --reload --port=8000
```
### Creating a Run Report Request

You create a run report requet, which will then crate the 1 or more workflow
executions required by sending a request to the HTTP endpoint.  You can do this
via a cURL statement, like the one below.

```
curl -X POST 'http://127.0.0.1:8000/api/run_report' \
  -H 'Content-Type: application/json' \
  -d '{
    "sources": [
      "YOUTUBE_VIDEO",
      "YOUTUBE_COMMENT"
    ],
    "data_output": "SENTIMENT_SCORE",
    "topic": "Acme Widgets",
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-12-31T23:59:59Z",
    "include_justifications": true
  }'
```