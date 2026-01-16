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
  project   = var.project_id
  secret_id = "DB-HOST"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "youtube_api_key" {
  project   = var.project_id
  secret_id = "API-YOUTUBE-KEY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "postgres_username_version" {
  project     = var.project_id
  secret      = google_secret_manager_secret.postgres_username.id
  secret_data = var.db_username

  depends_on = [google_secret_manager_secret.postgres_username]
}

resource "google_secret_manager_secret_version" "postgres_password_version" {
  project     = var.project_id
  secret      = google_secret_manager_secret.postgres_password.id
  secret_data = var.db_password

  depends_on = [google_secret_manager_secret.postgres_password]
}

resource "google_secret_manager_secret_version" "postgres_host_version" {
  project     = var.project_id
  secret      = google_secret_manager_secret.postgres_host.id
  secret_data = google_sql_database_instance.social_pulse_postgres_db_server.private_ip_address

  depends_on = [google_secret_manager_secret.postgres_host]
}

resource "google_secret_manager_secret_version" "youtube_api_key_version" {
  project     = var.project_id
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
