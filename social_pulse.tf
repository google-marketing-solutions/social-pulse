# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  timespec              = formatdate("MMDDYYYYhhmmss", timestamp())
  run_image_name        = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-analysis-run:latest"
  wfe_image_name        = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-analysis-wfe:latest"
  poller_image_name     = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-analysis-poller:latest"
  dbmigraion_image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-analysis-dbmigration:latest"

  report_api_image_name         = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-report-api:latest"
  report_dbmigration_image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-report-dbmigration:latest"
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

resource "google_pubsub_topic_iam_member" "scheduler_publisher_role" {
  topic      = google_pubsub_topic.poller_topic.name
  project    = var.project_id
  role       = "roles/pubsub.publisher"
  member     = "serviceAccount:${google_service_account.social-pulse-sa.email}"
  depends_on = [google_pubsub_topic.poller_topic]
}

resource "google_cloud_run_service_iam_member" "cloud_run_invoker_role" {
  project  = var.project_id
  location = var.region
  service  = google_cloud_run_v2_service.sp-analysis-poller.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.social-pulse-sa.email}"
}

# Storage bucket for source code
resource "google_storage_bucket" "source_code_bucket" {
  name                        = "social-pulse-source-code-${formatdate(local.timespec, timestamp())}"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
}

# Create a zip archive of the source code folder
data "archive_file" "source_zip" {
  type        = "zip"
  output_path = "social_pulse.zip"
  source_dir  = "."

  excludes = [
    "**/__pycache__",
    "**/dist",
    "*.egg-info",
    "**/.vscode",
    "**/.coverage",
    "**/*_pb2.py",
    "**/.env",
    "*.tfstate",
    "*.tfstate.backup",
    ".terraform",
    ".terraform.lock.hcl",
    "social_pulse.zip"
  ]
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


# Setup topics for pub/sub events
# -- Create a Pub/Sub topic for triggering the WorkflowExecutor
resource "google_pubsub_topic" "workflow_executor_topic" {
  project = var.project_id
  name    = "workflow_executor_topic"
}

# -- Create a Pub/Sub topci for triggering the Poller
resource "google_pubsub_topic" "poller_topic" {
  project = var.project_id
  name    = "poller_topic"
}

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
  name     = var.db_username
  instance = google_sql_database_instance.social_pulse_postgres_db_server.name
  password = var.db_password
}

# -- Create the DB for the Analysis services
resource "google_sql_database" "analysis_db" {
  name      = "analysis-database"
  instance  = google_sql_database_instance.social_pulse_postgres_db_server.name
  charset   = "UTF8"
  collation = "en_US.UTF8"
  project   = var.project_id
}

# -- Create the DB for the Reporting services
resource "google_sql_database" "reporting_db" {
  name      = "reporting-database"
  instance  = google_sql_database_instance.social_pulse_postgres_db_server.name
  charset   = "UTF8"
  collation = "en_US.UTF8"
  project   = var.project_id
}

# BigQuery Dataset
resource "google_bigquery_dataset" "social_pulse_sentiment_dataset" {
  dataset_id    = "social_pulse_sentiment_data"
  friendly_name = "Social Pulse Sentiment Data"
  description   = "Dataset for social pulse sentiment analysis data"
  location      = var.region
  project       = var.project_id

  access {
    role          = "OWNER"
    user_by_email = "social-pulse-sa@${var.project_id}.iam.gserviceaccount.com"
  }

  depends_on = [
    google_service_account.social-pulse-sa
  ]
}

# Create an Artifact Registry repository for the container image
resource "google_artifact_registry_repository" "my_repo" {
  project       = var.project_id
  location      = "us-central1"
  repository_id = "cloud-run-repo"
  format        = "DOCKER"
}



# Setup Docker build and deployments
# -- Authorize Docker
resource "null_resource" "auth_docker" {
  provisioner "local-exec" {
    command = "gcloud auth configure-docker ${google_artifact_registry_repository.my_repo.location}-docker.pkg.dev"
  }
}

# -- Build Docker image for the Runner
resource "null_resource" "build_run_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command     = <<EOT
      docker build \
        -f ./Dockerfile.analysis.run \
        -t ${local.run_image_name} \
        .
    EOT
    working_dir = path.module
  }
  depends_on = [null_resource.auth_docker, google_artifact_registry_repository.my_repo]
}

# -- Build Docker image for the Reporting API backend
resource "null_resource" "build_reporting_api_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command     = <<EOT
      docker build \
        -f ./Dockerfile.report.api \
        -t ${local.report_api_image_name} \
        .
    EOT
    working_dir = path.module
  }
  depends_on = [null_resource.auth_docker, google_artifact_registry_repository.my_repo]
}

# -- Build Docker image for the WFE Executor
resource "null_resource" "build_wfe_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command     = <<EOT
      docker build \
        -f ./Dockerfile.analysis.wfe \
        --build-arg PROJECT_ID=${var.project_id} \
        -t ${local.wfe_image_name} \
        .
    EOT
    working_dir = path.module
  }
  depends_on = [null_resource.auth_docker, google_artifact_registry_repository.my_repo]
}

# -- Build Docker image for the Poller
resource "null_resource" "build_poller_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command     = <<EOT
      docker build \
        -f ./Dockerfile.analysis.poller \
        --build-arg PROJECT_ID=${var.project_id} \
        -t ${local.poller_image_name} \
        .
    EOT
    working_dir = path.module
  }
  depends_on = [null_resource.auth_docker, google_artifact_registry_repository.my_repo]
}

# -- Build Docker image for the DB migraions
resource "null_resource" "build_db_migration_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command     = <<EOT
      docker build \
        -f ./Dockerfile.analysis.dbmigrations \
        --build-arg PROJECT_ID=${var.project_id} \
        -t ${local.dbmigraion_image_name} \
        .
    EOT
    working_dir = path.module
  }
  depends_on = [null_resource.auth_docker, google_artifact_registry_repository.my_repo]
}

# -- Build Docker image for the Reprt DB migraions
resource "null_resource" "build_report_db_migration_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command     = <<EOT
      docker build \
        -f ./Dockerfile.report.dbmigrations \
        --build-arg PROJECT_ID=${var.project_id} \
        -t ${local.report_dbmigration_image_name} \
        .
    EOT
    working_dir = path.module
  }
  depends_on = [null_resource.auth_docker, google_artifact_registry_repository.my_repo]
}

# -- Push Docker image for the Runner
resource "null_resource" "push_run_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command = "docker push ${local.run_image_name}"
  }
  depends_on = [null_resource.build_run_image]
}

# -- Push Docker image for the Reporting API
resource "null_resource" "push_reporting_api_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command = "docker push ${local.report_api_image_name}"
  }
  depends_on = [null_resource.build_run_image]
}

# -- Push Docker image for the poller
resource "null_resource" "push_poller_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command = "docker push ${local.poller_image_name}"
  }
  depends_on = [null_resource.build_poller_image]
}

# -- Push Docker image for the WFE Executor
resource "null_resource" "push_wfe_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command = "docker push ${local.wfe_image_name}"
  }
  depends_on = [null_resource.build_wfe_image]
}

# -- Push Docker image for the DB Migration
resource "null_resource" "push_db_migration_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command = "docker push ${local.dbmigraion_image_name}"
  }
  depends_on = [null_resource.build_db_migration_image]
}

# -- Push Docker image for the Report DB Migration
resource "null_resource" "push_report_db_migration_image" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command = "docker push ${local.report_dbmigration_image_name}"
  }
  depends_on = [null_resource.build_db_migration_image]
}


### Setup Runner, Reporting API, WFE Executior, Poller and DB Migration
### jobs/services

# -- Deploy the analysis runner service (Cloud Run Service)
resource "google_cloud_run_v2_service" "sp-analysis-run" {
  project             = var.project_id
  name                = "sp-analysis-run"
  location            = "us-central1"
  deletion_protection = false

  template {
    service_account = google_service_account.social-pulse-sa.email

    labels = {
      "source-code-hash" = data.archive_file.source_zip.output_md5
    }

    containers {
      image = local.run_image_name

      env {
        name = "DB__USERNAME"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.postgres_username.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "DB__PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.postgres_password.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "DB__HOST"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.postgres_host.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "API__YOUTUBE__KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.youtube_api_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name  = "APP_ENV"
        value = "prod"
      }
      env {
        name  = "DB__NAME"
        value = "analysis-database"
      }
      env {
        name  = "CLOUD__PROJECT_ID"
        value = var.project_id
      }
      env {
        name = "CLOUD__PROJECT_NUMBER"
        value = var.project_number
      }
      env {
        name = "CLOUD__REGION"
        value = var.region
      }
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }
  }

  depends_on = [
    null_resource.push_run_image,
    google_service_networking_connection.private_vpc_connection,
    google_vpc_access_connector.connector
  ]
}

# -- Deploy the reporting API service (Cloud Run Service)
resource "google_cloud_run_v2_service" "sp-reporting-api" {
  name                = "sp-reporting-api"
  project             = var.project_id
  location            = var.region
  deletion_protection = false

  template {
    service_account = google_service_account.social-pulse-sa.email

    labels = {
      "source-code-hash" = data.archive_file.source_zip.output_md5
    }

    containers {
      image = local.report_api_image_name

      env {
        name = "DB__USERNAME"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.postgres_username.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "DB__PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.postgres_password.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "DB__HOST"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.postgres_host.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "API__YOUTUBE__KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.youtube_api_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name  = "APP_ENV"
        value = "prod"
      }
      env {
        name  = "DB__NAME"
        value = "reporting-database"
      }
      env {
        name  = "CLOUD__PROJECT_ID"
        value = var.project_id
      }
      env {
        name = "CLOUD__PROJECT_NUMBER"
        value = var.project_number
      }
      env {
        name = "CLOUD__REGION"
        value = var.region
      }
    }
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }
  }

  depends_on = [
    null_resource.push_reporting_api_image,
    google_service_networking_connection.private_vpc_connection,
    google_vpc_access_connector.connector
  ]
}

# -- Deploy the poller service (Cloud Run Service)
resource "google_cloud_run_v2_service" "sp-analysis-poller" {
  project             = var.project_id
  location            = var.region
  name                = "sp-analysis-poller"
  description         = "Scheduled poller, triggered every 10 mins."
  deletion_protection = false

  template {
    service_account = google_service_account.social-pulse-sa.email

    labels = {
      "source-code-hash" = data.archive_file.source_zip.output_md5
    }

    containers {
      image = local.poller_image_name

      env {
        name = "DB__USERNAME"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.postgres_username.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "DB__PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.postgres_password.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "DB__HOST"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.postgres_host.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "API__YOUTUBE__KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.youtube_api_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name  = "APP_ENV"
        value = "prod"
      }
      env {
        name  = "DB__NAME"
        value = "analysis-database"
      }
      env {
        name  = "CLOUD__PROJECT_ID"
        value = var.project_id
      }
      env {
        name = "CLOUD__PROJECT_NUMBER"
        value = var.project_number
      }
      env {
        name = "CLOUD__REGION"
        value = var.region
      }
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }
  }

  depends_on = [
    null_resource.push_poller_image,
    google_service_networking_connection.private_vpc_connection,
    google_vpc_access_connector.connector
  ]
}

# -- Setup the scheduler to call the Poller service
resource "google_cloud_scheduler_job" "poller_scheduler" {
  project = var.project_id
  region  = var.region
  name    = "poller-scheduler-cron"

  # Run every 5 minutes
  schedule  = "*/5 * * * *"
  time_zone = "UTC"

  http_target {
    # URI uses the newly deployed Cloud Run Service URL + the /poller endpoint
    uri         = "${google_cloud_run_v2_service.sp-analysis-poller.uri}/poller"
    http_method = "POST"

    # Send a simple body to satisfy POST requirements, though it's optional
    body = base64encode("{}")
    headers = {
      "Content-Type" = "application/json"
    }

    oidc_token {
      service_account_email = google_service_account.social-pulse-sa.email
      audience              = google_cloud_run_v2_service.sp-analysis-poller.uri
    }
  }

  depends_on = [
    google_cloud_run_v2_service.sp-analysis-poller
  ]
}

# -- Deploy the analysis WFE Executor job (Cloud Run Job)
resource "google_cloud_run_v2_job" "sp-analysis-wfe" {
  name                = "sp-analysis-wfe"
  project             = var.project_id
  location            = var.region
  deletion_protection = false

  template {
    labels = {
      "source-code-hash" = data.archive_file.source_zip.output_md5
    }

    # Job template block
    template {
      service_account = google_service_account.social-pulse-sa.email
      max_retries     = 1
      timeout         = "3600s"

      containers {
        image   = local.wfe_image_name
        command = ["python", "api/workflow_executor.py"]
        args    = ["$(EXECUTION_ID)"]

        resources {
          limits = {
            "memory" = "4Gi"
          }
        }

        env {
          name  = "EXECUTION_ID"
          value = ""
        }

        env {
          name = "DB__USERNAME"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.postgres_username.secret_id
              version = "latest"
            }
          }
        }
        env {
          name = "DB__PASSWORD"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.postgres_password.secret_id
              version = "latest"
            }
          }
        }
        env {
          name = "DB__HOST"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.postgres_host.secret_id
              version = "latest"
            }
          }
        }
        env {
          name = "API__YOUTUBE__KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.youtube_api_key.secret_id
              version = "latest"
            }
          }
        }
        env {
          name  = "APP_ENV"
          value = "prod"
        }
        env {
          name  = "DB__NAME"
          value = "analysis-database"
        }
        env {
          name  = "CLOUD__PROJECT_ID"
          value = var.project_id
        }
        env {
          name = "CLOUD__PROJECT_NUMBER"
          value = var.project_number
        }
        env {
          name = "CLOUD__REGION"
          value = var.region
        }
      }

      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "ALL_TRAFFIC" # Ensures all traffic, including DB traffic, goes through the VPC
      }
    }
  }

  depends_on = [
    null_resource.push_wfe_image,
    google_service_networking_connection.private_vpc_connection,
    google_vpc_access_connector.connector
  ]
}

# -- Deply DB Migration job (Cloud Run Job)
resource "google_cloud_run_v2_job" "analysis_migration_job" {
  project             = var.project_id
  name                = "sp-analysis-migration-job"
  location            = var.region
  deletion_protection = false

  template {
    labels = {
      "source-code-hash" = data.archive_file.source_zip.output_md5
    }

    # Job template block
    template {
      service_account = google_service_account.social-pulse-sa.email
      containers {
        image = local.dbmigraion_image_name

        command = ["yoyo"]
        args = [
          "apply",
          "-vv",
          "--batch",
          "--no-cache",
          "--database=postgresql://${var.db_username}:${var.db_password}@${google_sql_database_instance.social_pulse_postgres_db_server.private_ip_address}/${google_sql_database.analysis_db.name}",
          "./db-migrations",
        ]
      }

      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "ALL_TRAFFIC"
      }
    }
  }

  depends_on = [
    google_sql_database.analysis_db,
    null_resource.push_db_migration_image,
    google_service_networking_connection.private_vpc_connection,
    google_vpc_access_connector.connector
  ]
}

# -- Deply Report DB Migration job (Cloud Run Job)
resource "google_cloud_run_v2_job" "report_migration_job" {
  project             = var.project_id
  name                = "sp-report-migration-job"
  location            = var.region
  deletion_protection = false

  template {
    labels = {
      "source-code-hash" = data.archive_file.source_zip.output_md5
    }

    # Job template block
    template {
      service_account = google_service_account.social-pulse-sa.email
      containers {
        image = local.report_dbmigration_image_name

        command = ["yoyo"]
        args = [
          "apply",
          "-vv",
          "--batch",
          "--no-cache",
          "--database=postgresql://${var.db_username}:${var.db_password}@${google_sql_database_instance.social_pulse_postgres_db_server.private_ip_address}/${google_sql_database.reporting_db.name}",
          "./db-migrations",
        ]
      }

      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "ALL_TRAFFIC"
      }
    }
  }

  depends_on = [
    google_sql_database.analysis_db,
    null_resource.push_report_db_migration_image,
    google_service_networking_connection.private_vpc_connection,
    google_vpc_access_connector.connector
  ]
}

resource "google_vpc_access_connector" "connector" {
  name          = "sp-vpc-connector"
  region        = "us-central1"
  ip_cidr_range = "10.8.0.0/28" # A non-overlapping range within your VPC
  network       = google_compute_network.vpc_network.self_link
  min_instances = 2
  max_instances = 10
}

# -- Set up needed screts needed by the app to configure connectsions
# ---  1) Create secret variables
# ---  2) Populate with values from the deployment
# ---  3) Give the service account access to them
resource "google_secret_manager_secret" "postgres_username" {
  project   = var.project_id
  secret_id = "DB-USERNAME"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "postgres_password" {
  project   = var.project_id
  secret_id = "DB-PASSWORD"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "postgres_host" {
  secret_id = "DB-HOST"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "youtube_api_key" {
  secret_id = "API-YOUTUBE-KEY"

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

resource "google_secret_manager_secret_version" "postgres_host_version" {
  secret      = google_secret_manager_secret.postgres_host.id
  secret_data = google_sql_database_instance.social_pulse_postgres_db_server.private_ip_address

  depends_on = [google_secret_manager_secret.postgres_host]
}

resource "google_secret_manager_secret_version" "youtube_api_key_version" {
  secret      = google_secret_manager_secret.youtube_api_key.id
  secret_data = var.yt_api_key

  depends_on = [google_secret_manager_secret.youtube_api_key]
}

resource "google_secret_manager_secret_iam_member" "postgres_username_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.postgres_username.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.social-pulse-sa.email}"
}

resource "google_secret_manager_secret_iam_member" "postgres_password_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.postgres_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.social-pulse-sa.email}"
}

resource "google_secret_manager_secret_iam_member" "postgres_host_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.postgres_host.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.social-pulse-sa.email}"
}

resource "google_secret_manager_secret_iam_member" "youtube_api_key_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.youtube_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.social-pulse-sa.email}"
}


# Output relevant information
output "project_id" {
  description = "The ID of the GCP project."
  value       = var.project_id
}

output "social_pulse_postgres_db_server_connection_name" {
  description = "The connection name for the analysis PostgreSQL instance."
  value       = google_sql_database_instance.social_pulse_postgres_db_server.connection_name
}

output "social_pulse_postgres_db_server_host" {
  description = "The host ip for the analysis PostgreSQL instance."
  value       = google_sql_database_instance.social_pulse_postgres_db_server.private_ip_address
}

output "bigquery_dataset_id" {
  description = "The ID of the BigQuery dataset."
  value       = google_bigquery_dataset.social_pulse_sentiment_dataset.dataset_id
}

output "pubsub_topic_name" {
  description = "The Pub/Sub topic name to publish to WFE Executor"
  value       = google_pubsub_topic.workflow_executor_topic.name
}
