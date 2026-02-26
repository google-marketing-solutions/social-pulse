# PostgreSQL databases for analysis and reporting metadata (Cloud SQL Instances)
# -- Create the Postgres SQL Server
resource "google_sql_database_instance" "social_pulse_postgres_db_server" {
  name             = "analysis-postgres-db-instance"
  database_version = "POSTGRES_14"
  region           = var.region
  project          = var.project_id
  settings {
    tier = "db-f1-micro" # Smallest instance type for testing
    ip_configuration {
      ipv4_enabled    = true
      private_network = google_compute_network.vpc_network.self_link
    }
    backup_configuration {
      enabled            = true
      binary_log_enabled = false # Not applicable for PostgreSQL
      start_time         = "03:00"
    }
    availability_type = "REGIONAL" # Or "ZONAL"
  }
  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# -- Create the user to access all DB instances
resource "google_sql_user" "postgres_db_user" {
  project  = var.project_id
  name     = var.db_username
  instance = google_sql_database_instance.social_pulse_postgres_db_server.name
  password = var.db_password

  depends_on = [google_sql_database_instance.social_pulse_postgres_db_server]
}

# -- Create the DB for the Analysis services
resource "google_sql_database" "analysis_db" {
  name      = "analysis-database"
  instance  = google_sql_database_instance.social_pulse_postgres_db_server.name
  charset   = "UTF8"
  collation = "en_US.UTF8"
  project   = var.project_id

  depends_on = [google_sql_database_instance.social_pulse_postgres_db_server]
}

# -- Create the DB for the Reporting services
resource "google_sql_database" "reporting_db" {
  name      = "reporting-database"
  instance  = google_sql_database_instance.social_pulse_postgres_db_server.name
  charset   = "UTF8"
  collation = "en_US.UTF8"
  project   = var.project_id

  depends_on = [google_sql_database_instance.social_pulse_postgres_db_server]
}

# BigQuery Dataset
resource "google_bigquery_dataset" "social_pulse_sentiment_dataset" {
  dataset_id    = var.bq_dataset_name
  location      = var.region
  project       = var.project_id
  friendly_name = "Gemini Social Sentiment Analyzer Sentiment Data"
  description   = "Dataset for Gemini Social Sentiment Analyzer data"

  access {
    role          = "OWNER"
    user_by_email = "social-pulse-sa@${var.project_id}.iam.gserviceaccount.com"
  }

  depends_on = [google_service_account.social-pulse-sa]
}
