## Local Developement

### Setting up environment

1. Create a virtual environmnet for the microservice.

2. Install the required packages.
   ```
   pip install -r requirements.txt
   ```

3. Create a .env file in the microservice root directory, and copy and paste
   the following into the file.  Then provide your values as instructed below.
   ```
   # Cloud Settings
   CLOUD.PROJECT_ID=[Your GCP project ID]]

   # API Settings
   API.YOUTUBE.KEY=[Your API key, from your GCP project]

   # Database Settings
   DB.PASSWORD=[Your DB password]
   DB.NAME=social_pulse_db
   ```


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
