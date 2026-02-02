# Storage bucket for source code
resource "google_storage_bucket" "source_code_bucket" {
  name                        = "social-pulse-source-code-${formatdate(local.timespec, timestamp())}"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
}

# Upload the zip archive to the GCS bucket
resource "google_storage_bucket_object" "source_zip_object" {
  name         = "social_pulse.zip"
  bucket       = google_storage_bucket.source_code_bucket.name
  source       = data.archive_file.source_zip.output_path
  content_type = "application/zip"

  depends_on = [google_storage_bucket.source_code_bucket]
}

# Create an Artifact Registry repository for the container image
resource "google_artifact_registry_repository" "my_repo" {
  project       = var.project_id
  location      = "us-central1"
  repository_id = "sp-cloud-run-repo"
  format        = "DOCKER"
}

# Create an Artifact Registry repository for Python packages
resource "google_artifact_registry_repository" "python_repo" {
  project       = var.project_id
  location      = "us-central1"
  repository_id = "sp-python-repo"
  format        = "PYTHON"
}
