locals {
  run_image_name        = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-analysis-run:latest"
  wfe_image_name        = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-analysis-wfe:latest"
  poller_image_name     = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-analysis-poller:latest"
  dbmigraion_image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-analysis-dbmigration:latest"

  report_api_image_name         = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-report-api:latest"
  report_dbmigration_image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-report-dbmigration:latest"
  report_ui_image_name          = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.my_repo.repository_id}/sp-report-ui:latest"
}

module "sp_analysis_run" {
  source                = "./modules/cloud_run_service"
  project_id            = var.project_id
  location              = var.region
  service_name          = "sp-analysis-run"
  image                 = local.run_image_name
  service_account_email = google_service_account.social-pulse-sa.email
  vpc_connector_id      = google_vpc_access_connector.connector.id
  secret_env_vars = {
    "DB__USERNAME"      = google_secret_manager_secret.postgres_username.secret_id
    "DB__PASSWORD"      = google_secret_manager_secret.postgres_password.secret_id
    "DB__HOST"          = google_secret_manager_secret.postgres_host.secret_id
    "API__YOUTUBE__KEY" = google_secret_manager_secret.youtube_api_key.secret_id
  }
  env_vars = {
    "APP_ENV"               = "prod"
    "DB__NAME"              = "analysis-database"
    "CLOUD__PROJECT_ID"     = var.project_id
    "CLOUD__PROJECT_NUMBER" = var.project_number
    "CLOUD__REGION"         = var.region
    "CLOUD__DATASET_NAME"   = var.bq_dataset_name
  }
  labels = {
    "source-code-hash" = data.archive_file.source_zip.output_md5
  }
  min_instance_count = 1

  depends_on = [google_service_account.social-pulse-sa,
    google_vpc_access_connector.connector,
    google_secret_manager_secret_version.postgres_username_version,
    google_secret_manager_secret_version.postgres_password_version,
    google_secret_manager_secret_version.postgres_host_version,
  google_secret_manager_secret_version.youtube_api_key_version]
}

module "sp_reporting_api" {
  source                = "./modules/cloud_run_service"
  project_id            = var.project_id
  location              = var.region
  service_name          = "sp-reporting-api"
  image                 = local.report_api_image_name
  service_account_email = google_service_account.social-pulse-sa.email
  vpc_connector_id      = google_vpc_access_connector.connector.id
  secret_env_vars = {
    "DB__USERNAME"      = google_secret_manager_secret.postgres_username.secret_id
    "DB__PASSWORD"      = google_secret_manager_secret.postgres_password.secret_id
    "DB__HOST"          = google_secret_manager_secret.postgres_host.secret_id
    "API__YOUTUBE__KEY" = google_secret_manager_secret.youtube_api_key.secret_id
  }
  env_vars = {
    "APP_ENV"               = "prod"
    "DB__NAME"              = "reporting-database"
    "CLOUD__PROJECT_ID"     = var.project_id
    "CLOUD__PROJECT_NUMBER" = var.project_number
    "CLOUD__REGION"         = var.region
    "CLOUD__DATASET_NAME"   = var.bq_dataset_name
  }
  labels = {
    "source-code-hash" = data.archive_file.source_zip.output_md5
  }

  min_instance_count = 1

  depends_on = [google_service_account.social-pulse-sa,
    google_vpc_access_connector.connector,
    google_secret_manager_secret_version.postgres_username_version,
    google_secret_manager_secret_version.postgres_password_version,
    google_secret_manager_secret_version.postgres_host_version,
  google_secret_manager_secret_version.youtube_api_key_version]
}

module "sp_reporting_ui" {
  source                = "./modules/cloud_run_service"
  project_id            = var.project_id
  location              = var.region
  service_name          = "sp-reporting-ui"
  image                 = local.report_ui_image_name
  service_account_email = google_service_account.social-pulse-sa.email
  vpc_connector_id      = google_vpc_access_connector.connector.id
  env_vars = {
    "REPORTING_API_URL" = module.sp_reporting_api.uri
  }
  labels = {
    "source-code-hash" = data.archive_file.source_zip.output_md5
  }

  depends_on = [google_service_account.social-pulse-sa,
    google_vpc_access_connector.connector,
  module.sp_reporting_api]
  min_instance_count = 1
}

resource "google_cloud_run_service_iam_member" "api_public_access" {
  project  = var.project_id
  location = var.region
  service  = module.sp_reporting_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"

  depends_on = [module.sp_reporting_api]
}

resource "google_cloud_run_service_iam_member" "ui_public_access" {
  project  = var.project_id
  location = var.region
  service  = module.sp_reporting_ui.name
  role     = "roles/run.invoker"
  member   = "allUsers"

  depends_on = [module.sp_reporting_ui]
}


module "sp_analysis_poller" {
  source                = "./modules/cloud_run_service"
  project_id            = var.project_id
  location              = var.region
  service_name          = "sp-analysis-poller"
  image                 = local.poller_image_name
  service_account_email = google_service_account.social-pulse-sa.email
  vpc_connector_id      = google_vpc_access_connector.connector.id
  secret_env_vars = {
    "DB__USERNAME"      = google_secret_manager_secret.postgres_username.secret_id
    "DB__PASSWORD"      = google_secret_manager_secret.postgres_password.secret_id
    "DB__HOST"          = google_secret_manager_secret.postgres_host.secret_id
    "API__YOUTUBE__KEY" = google_secret_manager_secret.youtube_api_key.secret_id
  }
  env_vars = {
    "APP_ENV"               = "prod"
    "DB__NAME"              = "analysis-database"
    "CLOUD__PROJECT_ID"     = var.project_id
    "CLOUD__PROJECT_NUMBER" = var.project_number
    "CLOUD__REGION"         = var.region
    "CLOUD__DATASET_NAME"   = var.bq_dataset_name
  }
  labels = {
    "source-code-hash" = data.archive_file.source_zip.output_md5
  }

  min_instance_count = 1

  depends_on = [google_service_account.social-pulse-sa,
    google_vpc_access_connector.connector,
    google_secret_manager_secret_version.postgres_username_version,
    google_secret_manager_secret_version.postgres_password_version,
    google_secret_manager_secret_version.postgres_host_version,
  google_secret_manager_secret_version.youtube_api_key_version]
}

resource "google_cloud_run_service_iam_member" "cloud_run_invoker_role" {
  project  = var.project_id
  location = var.region
  service  = module.sp_analysis_poller.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.social-pulse-sa.email}"

  depends_on = [google_service_account.social-pulse-sa,
  module.sp_analysis_poller]
}

resource "google_cloud_scheduler_job" "poller_scheduler" {
  project   = var.project_id
  region    = var.region
  name      = "poller-scheduler-cron"
  schedule  = "*/5 * * * *"
  time_zone = "UTC"
  http_target {
    uri         = "${module.sp_analysis_poller.uri}/poller"
    http_method = "POST"
    body        = base64encode("{}")
    headers = {
      "Content-Type" = "application/json"
    }
    oidc_token {
      service_account_email = google_service_account.social-pulse-sa.email
      audience              = module.sp_analysis_poller.uri
    }
  }
  depends_on = [module.sp_analysis_poller,
    google_cloud_run_service_iam_member.cloud_run_invoker_role,
  google_service_account.social-pulse-sa]
}

module "sp_analysis_wfe" {
  source                = "./modules/cloud_run_job"
  project_id            = var.project_id
  location              = var.region
  job_name              = "sp-analysis-wfe"
  image                 = local.wfe_image_name
  service_account_email = google_service_account.social-pulse-sa.email
  vpc_connector_id      = google_vpc_access_connector.connector.id
  command               = ["python", "api/workflow_executor.py"]
  args                  = ["$(EXECUTION_ID)"]
  secret_env_vars = {
    "DB__USERNAME"      = google_secret_manager_secret.postgres_username.secret_id
    "DB__PASSWORD"      = google_secret_manager_secret.postgres_password.secret_id
    "DB__HOST"          = google_secret_manager_secret.postgres_host.secret_id
    "API__YOUTUBE__KEY" = google_secret_manager_secret.youtube_api_key.secret_id
  }
  env_vars = {
    "EXECUTION_ID"          = ""
    "APP_ENV"               = "prod"
    "DB__NAME"              = "analysis-database"
    "CLOUD__PROJECT_ID"     = var.project_id
    "CLOUD__PROJECT_NUMBER" = var.project_number
    "CLOUD__REGION"         = var.region
    "CLOUD__DATASET_NAME"   = var.bq_dataset_name
  }
  labels = {
    "source-code-hash" = data.archive_file.source_zip.output_md5
  }
  max_retries = 1
  timeout     = "3600s"

  depends_on = [google_service_account.social-pulse-sa,
    google_vpc_access_connector.connector,
    google_secret_manager_secret_version.postgres_username_version,
    google_secret_manager_secret_version.postgres_password_version,
    google_secret_manager_secret_version.postgres_host_version,
  google_secret_manager_secret_version.youtube_api_key_version]
}

module "analysis_migration_job" {
  source                = "./modules/cloud_run_job"
  project_id            = var.project_id
  location              = var.region
  job_name              = "sp-analysis-migration-job"
  image                 = local.dbmigraion_image_name
  service_account_email = google_service_account.social-pulse-sa.email
  vpc_connector_id      = google_vpc_access_connector.connector.id
  command               = ["yoyo"]
  args = [
    "apply",
    "-vv",
    "--batch",
    "--no-cache",
    "--database=postgresql://${var.db_username}:${var.db_password}@${google_sql_database_instance.social_pulse_postgres_db_server.private_ip_address}/${google_sql_database.analysis_db.name}",
    "./db-migrations",
  ]
  labels = {
    "source-code-hash" = data.archive_file.source_zip.output_md5
  }

  depends_on = [google_service_account.social-pulse-sa,
    google_vpc_access_connector.connector,
    google_sql_database_instance.social_pulse_postgres_db_server,
    google_secret_manager_secret_version.postgres_username_version,
    google_secret_manager_secret_version.postgres_password_version,
    google_secret_manager_secret_version.postgres_host_version,
  google_secret_manager_secret_version.youtube_api_key_version]
}

module "report_migration_job" {
  source                = "./modules/cloud_run_job"
  project_id            = var.project_id
  location              = var.region
  job_name              = "sp-report-migration-job"
  image                 = local.report_dbmigration_image_name
  service_account_email = google_service_account.social-pulse-sa.email
  vpc_connector_id      = google_vpc_access_connector.connector.id
  command               = ["yoyo"]
  args = [
    "apply",
    "-vv",
    "--batch",
    "--no-cache",
    "--database=postgresql://${var.db_username}:${var.db_password}@${google_sql_database_instance.social_pulse_postgres_db_server.private_ip_address}/${google_sql_database.reporting_db.name}",
    "./db-migrations",
  ]
  labels = {
    "source-code-hash" = data.archive_file.source_zip.output_md5
  }

  depends_on = [google_service_account.social-pulse-sa,
    google_vpc_access_connector.connector,
    google_sql_database_instance.social_pulse_postgres_db_server,
    google_secret_manager_secret_version.postgres_username_version,
    google_secret_manager_secret_version.postgres_password_version,
    google_secret_manager_secret_version.postgres_host_version,
  google_secret_manager_secret_version.youtube_api_key_version]
}
