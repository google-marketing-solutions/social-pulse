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

### Running the Command Line Sentiment Analaysis Tool

You execute the run_sentiment.py tool to run a workflow execution and generate sentiment analysis data.

```
./run_sentiment.py -h

usage: run_sentiment.py [-h] [-v] --source
                        {SOCIAL_MEDIA_SOURCE_UNKNOWN,SOCIAL_MEDIA_SOURCE_YOUTUBE_VIDEO,SOCIAL_MEDIA_SOURCE_YOUTUBE_COMMENT,SOCIAL_MEDIA_SOURCE_REDDIT_POST,SOCIAL_MEDIA_SOURCE_X_POST,SOCIAL_MEDIA_SOURCE_APP_STORE_REVIEW}
                        --topic TOPIC
                        [--outputs {SENTIMENT_DATA_TYPE_UNKNOWN,SENTIMENT_DATA_TYPE_SENTIMENT_SCORE,SENTIMENT_DATA_TYPE_JUSTIFICATION,SENTIMENT_DATA_TYPE_DISTRIBUTION} [{SENTIMENT_DATA_TYPE_UNKNOWN,SENTIMENT_DATA_TYPE_SENTIMENT_SCORE,SENTIMENT_DATA_TYPE_JUSTIFICATION,SENTIMENT_DATA_TYPE_DISTRIBUTION} ...]]
                        --start-date START_DATE [--end-date END_DATE]

Generate sentiment analysis for a given topic from a social media source.

options:
  -h, --help            show this help message and exit
  -v, --verbose         Increase output verbosity, by setting logging to DEBUG level.
  --source {SOCIAL_MEDIA_SOURCE_UNKNOWN,SOCIAL_MEDIA_SOURCE_YOUTUBE_VIDEO,SOCIAL_MEDIA_SOURCE_YOUTUBE_COMMENT,SOCIAL_MEDIA_SOURCE_REDDIT_POST,SOCIAL_MEDIA_SOURCE_X_POST,SOCIAL_MEDIA_SOURCE_APP_STORE_REVIEW}
                        Social media content source to retrieve ('Youtube', 'Twitter', etc.).
  --topic TOPIC         Topic (brand, product or feature) to generate the sentiment analysis for.
  --outputs {SENTIMENT_DATA_TYPE_UNKNOWN,SENTIMENT_DATA_TYPE_SENTIMENT_SCORE,SENTIMENT_DATA_TYPE_JUSTIFICATION,SENTIMENT_DATA_TYPE_DISTRIBUTION} [{SENTIMENT_DATA_TYPE_UNKNOWN,SENTIMENT_DATA_TYPE_SENTIMENT_SCORE,SENTIMENT_DATA_TYPE_JUSTIFICATION,SENTIMENT_DATA_TYPE_DISTRIBUTION} ...]
                        Types of sentiment data to output. Defaults to sentiment score.
  --start-date START_DATE
                        Start date of the analysis window (format: YYYY-MM-DD).
  --end-date END_DATE   End date of the analysis window (format: YYYY-MM-DD). Defaults to today.
```

Please note the following when executing the run_sentiment.py CLI:

1.  Currently, only the SOCIAL_MEDIA_SOURCE_YOUTUBE_VIDEO and     SOCIAL_MEDIA_SOURCE_YOUTUBE_COMMENT content types are supported.

2. Currently, only the SENTIMENT_DATA_TYPE_SENTIMENT_SCORE output type is
supported.

3. Whatever value you provide for the topic parameter is used as-is for doing a
search on the relevant social media content.  For example, if the topic is set
to “Product X text-to-image” and the source is Youtube videos, then a search
will be done on Youtube with “Product X text-to-image” to find the videos and
comments to analyze for sentiment.
