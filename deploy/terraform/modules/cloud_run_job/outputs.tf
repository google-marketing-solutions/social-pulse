output "job_id" {
  description = "The ID of the Cloud Run job."
  value       = google_cloud_run_v2_job.default.id
}

output "name" {
  description = "The name of the Cloud Run job."
  value       = google_cloud_run_v2_job.default.name
}
