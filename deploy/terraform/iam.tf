# Create a new service account

resource "google_artifact_registry_repository_iam_member" "sa_artifact_reader" {
  project    = google_artifact_registry_repository.my_repo.project
  location   = google_artifact_registry_repository.my_repo.location
  repository = google_artifact_registry_repository.my_repo.repository_id
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.social-pulse-sa.email}"

  depends_on = [google_service_account.social-pulse-sa]
}

resource "google_service_account" "social-pulse-sa" {
  project      = var.project_id
  account_id   = "social-pulse-sa"
  display_name = "Service account for social pulse"
}

# Grant the service account permissions (e.g., to be a project editor)
resource "google_project_iam_member" "service_account_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.social-pulse-sa.email}"

  depends_on = [google_service_account.social-pulse-sa]
}

resource "google_pubsub_topic_iam_member" "scheduler_publisher_role" {
  topic      = google_pubsub_topic.poller_topic.name
  project    = var.project_id
  role       = "roles/pubsub.publisher"
  member     = "serviceAccount:${google_service_account.social-pulse-sa.email}"
  depends_on = [google_pubsub_topic.poller_topic, google_service_account.social-pulse-sa]
}

data "google_project" "project" {}

resource "google_project_iam_member" "cloudbuild_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}
