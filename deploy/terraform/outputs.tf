output "analysis_run_service_url" {
  description = "The URL of the Analysis Run service."
  value       = module.sp_analysis_run.uri
}

output "reporting_api_url" {
  description = "The URL of the Reporting API service."
  value       = module.sp_reporting_api.uri
}

output "analysis_poller_url" {
  description = "The URL of the Analysis Poller service."
  value       = module.sp_analysis_poller.uri
}

output "reporting_ui_url" {
  description = "The URL of the Reporting UI service."
  value       = module.sp_reporting_ui.uri
}
