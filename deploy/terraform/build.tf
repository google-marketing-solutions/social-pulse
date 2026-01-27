locals {
  timespec = formatdate("MMDDYYYYhhmmss", timestamp())
}

# Create a zip archive of the source code folder
data "archive_file" "source_zip" {
  type        = "zip"
  output_path = "/tmp/social_pulse.zip" # Output to tmp to avoid including in archive
  source_dir  = "../../"

  excludes = [
    "**/__pycache__",
    "*.egg-info",
    "**/.vscode",
    "**/.coverage",
    "**/*_pb2.py",
    "**/.env",
    "*.tfstate",
    "*.tfstate.backup",
    ".terraform",
    ".terraform.lock.hcl",
    "social_pulse.zip",
    "deploy/terraform/**", # Exclude terraform files
    ".git/**"             # Exclude git directory
  ]
}

# This null_resource will trigger the Cloud Build pipeline
# to build and push all Docker images.
resource "null_resource" "cloud_build_trigger" {
  triggers = {
    # This will trigger the build every time the source code changes
    source_code_hash = data.archive_file.source_zip.output_md5
  }

  provisioner "local-exec" {
    command = <<EOT
      gcloud builds submit \
        --config ../../deploy/cloudbuild.yaml \
        --substitutions=_REGION=${var.region},_REPOSITORY=${google_artifact_registry_repository.my_repo.repository_id} \
        --project=${var.project_id} \
        ${data.archive_file.source_zip.output_path}
    EOT
    working_dir = path.module
  }

  depends_on = [
    google_project_iam_member.cloudbuild_artifact_writer,
    google_storage_bucket_object.source_zip_object,
  ]
}
