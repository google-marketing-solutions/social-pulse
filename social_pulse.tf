# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# GCP Project
# This resource creates a new GCP project. If you already have a project,
# you can comment this out and just use the existing project ID in var.project_id.
#resource "google_project" "new_project" {
#  count       = var.create_new_project ? 1 : 0 # Only create if create_new_project is true
#  name        = var.project_id
#  project_id  = var.project_id
#  org_id      = var.org_id # Replace with your organization ID if creating a new project
#  billing_account = var.billing_account_id # Replace with your billing account ID
#}

locals {
  timespec = formatdate("MMDDYYYYhhmmss", timestamp())
  run_image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-analysis-run:latest"
  wfe_image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-analysis-wfe:latest"
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

# Storage bucket for source code
resource "google_storage_bucket" "source_code_bucket" {
  name          = "social-pulse-source-code-${formatdate(local.timespec, timestamp())}"
  location      = var.region
  project       = var.project_id
  uniform_bucket_level_access = true
}

# Create a zip archive of the source code folder
data "archive_file" "source_zip" {
  type        = "zip"
  output_path = "social_pulse.zip"
  source_dir  = "."
}

# Upload the zip archive to the GCS bucket
resource "google_storage_bucket_object" "source_zip_object" {
  name         = "social_pulse.zip"
  bucket       = google_storage_bucket.source_code_bucket.name
  source       = data.archive_file.source_zip.output_path
  content_type = "application/zip"
}

# Set up VPC network
resource "google_compute_network" "vpc_network" {
  name                    = "sp-vpc-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "vpc_subnet" {
  name          = "sp-vpc-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = "us-central1"
  network       = google_compute_network.vpc_network.self_link
}

resource "google_compute_global_address" "private_ip_alloc" {
  name          = "sp-cloudsql-private-ip-alloc"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 20
  network       = google_compute_network.vpc_network.self_link
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc_network.self_link
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
  depends_on              = [google_compute_global_address.private_ip_alloc]
}

# PostgreSQL Databases for analysis and reporting metadata (Cloud SQL Instances)
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
      private_network = google_compute_network.vpc_network.self_link
    }
    backup_configuration {
      enabled    = true
      start_time = "04:00"
    }
    availability_type = "REGIONAL"
  }
  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Database inside the reporting instance
resource "google_sql_database" "reporting_db" {
  name     = "reporting-database"
  instance = google_sql_database_instance.social_pulse_reporting_postgres_db.name
  charset  = "UTF8"
  collation = "en_US.UTF8"
  project  = var.project_id
}

# BigQuery Dataset
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
}

# Create an Artifact Registry repository for the container image
resource "google_artifact_registry_repository" "my_repo" {
  project      = var.project_id
  location     = "us-central1"
  repository_id = "cloud-run-repo"
  format       = "DOCKER"
}

resource "null_resource" "auth_docker" {
  provisioner "local-exec" {
    command = "gcloud auth configure-docker ${google_artifact_registry_repository.my_repo.location}-docker.pkg.dev"
  }
}

resource "null_resource" "build_run_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command     = "docker build -f ./Dockerfile.analysis.run --build-arg YOYO_DB_ACCESS_URL=postgresql://${var.db_username}:${var.db_password}@${google_sql_database_instance.social_pulse_analysis_postgres_db.public_ip_address}/analysis-database -t ${local.run_image_name} ."
    working_dir = path.module
  }
  depends_on = [null_resource.auth_docker, google_artifact_registry_repository.my_repo]

}

resource "null_resource" "build_wfe_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command     = "docker build -f ./Dockerfile.analysis.wfe --build-arg YOYO_DB_ACCESS_URL=postgresql://${var.db_username}:${var.db_password}@${google_sql_database_instance.social_pulse_analysis_postgres_db.public_ip_address}/reporting-database -t ${local.wfe_image_name} ."
    working_dir = path.module
  }
  depends_on = [null_resource.auth_docker, google_artifact_registry_repository.my_repo]

}

resource "null_resource" "push_run_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command = "docker push ${local.run_image_name}"
  }
  depends_on = [null_resource.build_run_image]
}

resource "null_resource" "push_wfe_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command = "docker push ${local.wfe_image_name}"
  }
  depends_on = [null_resource.build_wfe_image]
}

# Deploy the analysis run Cloud Run service
resource "google_cloud_run_v2_service" "sp-analysis-run" {
  project  = var.project_id
  name     = "sp-analysis-run"
  location = "us-central1"
  deletion_protection = false

  template {
    containers {
      image = "${local.run_image_name}"
    }
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Deploy the analysis wfe Cloud Run service
resource "google_cloud_run_v2_service" "sp-analysis-wfe" {
  project  = var.project_id
  name     = "sp-analysis-wfe"
  location = "us-central1"
  deletion_protection = false

  template {
    containers {
      image = "${local.run_image_name}"
    }
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_vpc_access_connector" "connector" {
  name          = "sp-vpc-connector"
  region        = "us-central1"
  ip_cidr_range = "10.8.0.0/28" # A non-overlapping range within your VPC
  network       = google_compute_network.vpc_network.self_link
  min_instances = 2
  max_instances = 10
}

resource "google_secret_manager_secret" "postgres_username" {
  project = var.project_id
  secret_id = "DB_USER"

  # Define replication policy (e.g., automatic replication)
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "postgres_password" {
  project = var.project_id
  secret_id = "DB_PASSWORD"

  # Define replication policy (e.g., automatic replication)
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "postgres_username_version" {
  secret      = google_secret_manager_secret.postgres_username.id
  secret_data = var.db_username

  depends_on = [google_secret_manager_secret.postgres_username]
}

resource "google_secret_manager_secret_version" "postgres_password_version" {
  secret      = google_secret_manager_secret.postgres_password.id
  secret_data = var.db_password

  depends_on = [google_secret_manager_secret.postgres_password]
}

resource "google_secret_manager_secret" "youtube_api_key_secret" {
  secret_id = "YT_API_KEY"

  # Define replication policy (e.g., automatic replication)
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "youtube_api_key_version" {
  secret      = google_secret_manager_secret.youtube_api_key_secret.id
  secret_data = var.yt_api_key

  depends_on = [google_secret_manager_secret.youtube_api_key_secret]
}

resource "google_secret_manager_secret" "analysis_db_host_secret" {
  secret_id = "ANALYSIS_DB_HOST"

  # Define replication policy (e.g., automatic replication)
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "analysis_db_host_version" {
  secret      = google_secret_manager_secret.analysis_db_host_secret.id
  secret_data = google_sql_database_instance.social_pulse_analysis_postgres_db.public_ip_address

  depends_on = [google_secret_manager_secret.analysis_db_host_secret]
}

resource "google_secret_manager_secret" "reporting_db_host_secret" {
  secret_id = "REPORTING_DB_HOST"

  # Define replication policy (e.g., automatic replication)
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "reporting_db_host_version" {
  secret      = google_secret_manager_secret.reporting_db_host_secret.id
  secret_data = google_sql_database_instance.social_pulse_reporting_postgres_db.public_ip_address

  depends_on = [google_secret_manager_secret.reporting_db_host_secret]
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

output "social_pulse_analysis_postgres_db_host" {
  description = "The host ip for the analysis PostgreSQL instance."
  value       = google_sql_database_instance.social_pulse_analysis_postgres_db.public_ip_address
}

output "social_pulse_reporting_postgres_db_connection_name" {
  description = "The connection name for the reporting PostgreSQL instance."
  value       = google_sql_database_instance.social_pulse_reporting_postgres_db.connection_name
}

output "social_pulse_reporting_postgres_db_host" {
  description = "The host ip for the reporting PostgreSQL instance."
  value       = google_sql_database_instance.social_pulse_reporting_postgres_db.public_ip_address
}

output "bigquery_dataset_id" {
  description = "The ID of the BigQuery dataset."
  value       = google_bigquery_dataset.social_pulse_dataset.dataset_id
}
