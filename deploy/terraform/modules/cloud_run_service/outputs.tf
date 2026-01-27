output "uri" {
  description = "The URI of the Cloud Run service."
  value       = google_cloud_run_v2_service.default.uri
}

output "service_id" {
  description = "The ID of the Cloud Run service."
  value       = google_cloud_run_v2_service.default.id
}

output "name" {
  description = "The name of the Cloud Run service."
  value       = google_cloud_run_v2_service.default.name
}
