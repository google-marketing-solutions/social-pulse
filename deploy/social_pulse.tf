# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. GCP Project
# This resource creates a new GCP project. If you already have a project,
# you can comment this out and just use the existing project ID in var.project_id.
#resource "google_project" "new_project" {
#  count       = var.create_new_project ? 1 : 0 # Only create if create_new_project is true
#  name        = var.project_id
#  project_id  = var.project_id
#  org_id      = var.org_id # Replace with your organization ID if creating a new project
#  billing_account = var.billing_account_id # Replace with your billing account ID
#}

# Enable necessary APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "bigquery.googleapis.com",
    "youtube.googleapis.com",
    "cloudbuild.googleapis.com", # Required for Cloud Functions deployment
    "artifactregistry.googleapis.com", # Required for Cloud Functions (Gen2)
    "storage.googleapis.com", # For Cloud Functions source code bucket
    "iam.googleapis.com", # For managing service accounts
  ])
  project = var.project_id
  service = each.key
  disable_on_destroy = false
}

resource "google_project_service" "cloud_build_api" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

# Create a new service account
resource "google_service_account" "social-pulse-sa" {
  account_id   = "social-pulse-sa"
  display_name = "Service account for social pulse"
}

# Grant the service account permissions (e.g., to be a project editor)
resource "google_project_iam_member" "service_account_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.social-pulse-sa.email}"
}

# Storage bucket for Cloud Functions source code
resource "google_storage_bucket" "functions_bucket" {
  name          = "social-pulse-cloud-functions-source"
  location      = var.region
  project       = var.project_id
  uniform_bucket_level_access = true
  depends_on = [google_project_service.apis]
}

# Create a zip archive of the source code folder
data "archive_file" "source_zip" {
  type        = "zip"
  output_path = "social_pulse.zip"
  source_dir  = "../../social_pulse"
}

# Upload the zip archive to the GCS bucket
resource "google_storage_bucket_object" "source_zip_object" {
  name         = "social_pulse.zip"
  bucket       = google_storage_bucket.functions_bucket.name
  source       = data.archive_file.source_zip.output_path
  content_type = "application/zip"
}

resource "google_secret_manager_secret" "postgres_credentials" {
  project = var.project_id
  secret_id = "postgres-db-credentials"

  # Define replication policy (e.g., automatic replication)
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

output "secret_id" {
  value = google_secret_manager_secret.youtube_api_key_secret.id
}

resource "google_secret_manager_secret_version" "postgres_credentials_version" {
  secret      = google_secret_manager_secret.postgres_credentials.id
  secret_data = jsonencode({
    username = var.db_username
    password = var.db_password
  })

  depends_on = [google_secret_manager_secret.postgres_credentials]
}

resource "google_secret_manager_secret" "youtube_api_key_secret" {
  secret_id = "youtube-api-key"

  # Define replication policy (e.g., automatic replication)
  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "youtube_api_key_version" {
  secret      = google_secret_manager_secret.youtube_api_key_secret.id
  secret_data = var.yt_api_key

  depends_on = [google_secret_manager_secret.youtube_api_key_secret]
}

# 3. PostgreSQL Databases for analysis and reporting metadata (Cloud SQL Instances)

# Analysis PostgreSQL instance
resource "google_sql_database_instance" "social_pulse_analysis_postgres_db" {
  name             = "analysis-postgres-db-instance"
  database_version = "POSTGRES_14"
  region           = var.region
  project          = var.project_id
  settings {
    tier = "db-f1-micro" # Smallest instance type for testing
    ip_configuration {
      ipv4_enabled = true
    }
    backup_configuration {
      enabled            = true
      binary_log_enabled = false # Not applicable for PostgreSQL
      start_time         = "03:00"
    }
    availability_type = "REGIONAL" # Or "ZONAL"
  }
  depends_on = [google_project_service.apis]
}

resource "google_sql_user" "postgres_db_user" {
  name     = var.db_username
  instance = google_sql_database_instance.social_pulse_analysis_postgres_db.name
  password = var.db_password
}

# Database inside the analysis instance
resource "google_sql_database" "analysis_db" {
  name     = "analysis-database"
  instance = google_sql_database_instance.social_pulse_analysis_postgres_db.name
  charset  = "UTF8"
  collation = "en_US.UTF8"
  project  = var.project_id
}

# Reprting PostgreSQL instance
resource "google_sql_database_instance" "social_pulse_reporting_postgres_db" {
  name             = "reporting-postgres-db-instance"
  database_version = "POSTGRES_14"
  region           = var.region
  project          = var.project_id
  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled = true
    }
    backup_configuration {
      enabled    = true
      start_time = "04:00"
    }
    availability_type = "REGIONAL"
  }
  depends_on = [google_project_service.apis]
}

# Database inside the reporting instance
resource "google_sql_database" "reporting_db" {
  name     = "reporting-database"
  instance = google_sql_database_instance.social_pulse_reporting_postgres_db.name
  charset  = "UTF8"
  collation = "en_US.UTF8"
  project  = var.project_id
}

# 4. BigQuery Dataset
resource "google_bigquery_dataset" "social_pulse_dataset" {
  dataset_id                  = "social_pulse_dataset"
  friendly_name               = "Social Pulse Sentiment Data"
  description                 = "Dataset for social pulse sentiment analysis data"
  location                    = var.region
  project                     = var.project_id
  default_table_expiration_ms = 3600000 # 1 hour
  access {
    role          = "OWNER"
    user_by_email = "social-pulse-sa@${var.project_id}.iam.gserviceaccount.com"
  }
  depends_on = [google_project_service.apis]
}

# Create an Artifact Registry repository for the container image
resource "google_artifact_registry_repository" "my_repo" {
  project      = var.project_id
  location     = "us-central1"
  repository_id = "cloud-run-repo"
  format       = "DOCKER"
}

locals {
  artifact_image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/my-app:latest"
}

resource "null_resource" "auth_docker" {
  provisioner "local-exec" {
    command = "gcloud auth configure-docker ${google_artifact_registry_repository.my_repo.location}-docker.pkg.dev"
  }
}

resource "null_resource" "build_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command     = "docker build -f ./Dockerfile --build-arg YOYO_DB_ACCESS_URL=${google_sql_database_instance.social_pulse_analysis_postgres_db.public_ip_address} -t us-central1-docker.pkg.dev/${var.project_id}/cloud-run-repo/my-app:latest ."
    working_dir = path.module
  }
  depends_on = [null_resource.auth_docker, google_artifact_registry_repository.my_repo]

}

resource "null_resource" "push_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command = "docker push ${local.artifact_image_name}"
  }
  depends_on = [null_resource.build_image]
}

# Deploy the Cloud Run service
resource "google_cloud_run_v2_service" "default" {
  project  = var.project_id
  name     = "my-cloud-run-service"
  location = "us-central1"

  template {
    containers {
      image = "${google_artifact_registry_repository.my_repo.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/my-app:latest"
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

}

# Output relevant information
output "project_id" {
  description = "The ID of the GCP project."
  value       = var.project_id
}

output "social_pulse_analysis_postgres_db_connection_name" {
  description = "The connection name for the analysis PostgreSQL instance."
  value       = google_sql_database_instance.social_pulse_analysis_postgres_db.connection_name
}

output "social_pulse_reporting_postgres_db_connection_name" {
  description = "The connection name for the reporting PostgreSQL instance."
  value       = google_sql_database_instance.social_pulse_reporting_postgres_db.connection_name
}

output "bigquery_dataset_id" {
  description = "The ID of the BigQuery dataset."
  value       = google_bigquery_dataset.social_pulse_dataset.dataset_id
}
