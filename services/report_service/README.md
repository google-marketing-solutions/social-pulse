## Architecture Overview

### Sequence/Status Diagram
+------------------+             +------------------+
|  Report Service  |             | Analysis Service |
|                  |             |                  |
+------------------+             +------------------+     +---------------+        +---------------+
         |                                |               | Workflow Exec |        | Workflow Exec |
         |                                |               |      1        |  ...   |      N        |
         |      create_dataset            |               +---------------+        +---------------+
         |------------------------------->|                      |                        |
         |[STATUS = COLLECTING_DATA]      |                      |                        |
         |                                |--------------------->|                        |
         |                                |<---------------------|                        |
         |                                |                      |                        |
         |                                |---------------------------------------------->|
         |                                |<----------------------------------------------|
         |                                |                      |                        |
         |      mark_data_collected       |                      |                        |
         |<-------------------------------|                      *                        *     +------------------+
         |[STATUS = DATA_COLLECTED]       |                                                     | RptSrvc:         |
         |                                |                                                     | Report Generator |
         |                                |                                                     +-   --------------+
         |                                |       generate_report                                         |
         |----------------------------------------------------------------------------------------------->|
         |[STATUS = GENERATING_REPORT]    |                                                               |
         |                                |                                                               |
         |                                |       mark_report_completed                                   |
         |<-----------------------------------------------------------------------------------------------|
         |[STATUS = COMPLETD]             |                                                               |
         |                                |                                                               |
         |                                |                                                               |
         |                                |                                                               *
         *                                *

## Local Developement

### Setting up environment

1. Create a virtual environmnet for the microservice.

2. Install the required packages.
   ```
   pip install \
      -r requirements.txt \
      -r requirements-dev.txt \
      --find-links=../shared_lib/dist
   ```

3. Create a .env file in the microservice root directory, and copy and paste
   the following into the file.  Then provide your values as instructed below.
   ```
   # Cloud Settings
   CLOUD__PROJECT_ID=[Your GCP project ID]

   # API Settings
   API__YOUTUBE__KEY=[Your API key, from your GCP project]

   # Database Settings
   DB__PASSWORD=[Your DB password]
   DB__NAME=social_pulse_reporting_db
   ```


### Setting up the reporting service PostgresDB

1. Install PostgresDB on your local system.

2. Create Social Pulse reporting service database and user.
   ```
   sudo -i -u postgres
   psql

   CREATE DATABASE social_pulse_reporting_db;
   CREATE USER social_pulse_reporting_user WITH PASSWORD '[Your DB passowrd]';
   GRANT ALL PRIVILEGES ON DATABASE social_pulse_reporting_db to social_pulse_reporting_user;
   \q
   ```

3. Log into the Social Pulse app DB and set up schema access
   ```
   psql -d social_pulse_reporting_db

   GRANT CREATE ON SCHEMA public TO social_pulse_reporting_user;
   GRANT USAGE ON SCHEMA public TO social_pulse_reporting_user;
   \q
   ```

4. Test connecting to the Social Pulse app DB as the user,
   and verify that the user has the proper access (the
   queries below should both return 't' for TRUE).
   ```
   psql -U social_pulse_reporting_user -d social_pulse_reporting_db -h localhost -W

   SELECT has_database_privilege('social_pulse_reporting_user', 'social_pulse_reporting_db', 'CONNECT');
   SELECT has_schema_privilege('social_pulse_reporting_user', 'public', 'CREATE');
   ```

5. Init Yoyo so it can create a `yoyo.ini` file for you to use when running
   your migrations.
   ```
   yoyo init \
      --database postgresql://social_pulse_reporting_user:[Your DB password]@localhost:5432/social_pulse_reporting_db \
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
cd services/report_service
pytest /tests

```

### Creating a Create New Report Request

```
curl -X POST http://localhost:8080/api/report \
  -v \
  -H "Content-Type: application/json" \
  -d '{
    "sources": [
      "YOUTUBE_VIDEO",
      "YOUTUBE_COMMENT"
    ],
    "data_output": "SENTIMENT_SCORE",
    "start_time": "2025-10-01T00:00:00Z",
    "end_time": "2025-10-06T12:00:00Z",
    "include_justifications": true,
    "topic": "Acme widgets"
  }'
```