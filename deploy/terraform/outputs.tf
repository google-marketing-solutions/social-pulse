# Output relevant information
output "project_id" {
  description = "The ID of the GCP project."
  value       = var.project_id
}

output "social_pulse_postgres_db_server_connection_name" {
  description = "The connection name for the analysis PostgreSQL instance."
  value       = google_sql_database_instance.social_pulse_postgres_db_server.connection_name

  depends_on = [google_sql_database_instance.social_pulse_postgres_db_server]
}

output "social_pulse_postgres_db_server_host" {
  description = "The host ip for the analysis PostgreSQL instance."
  value       = google_sql_database_instance.social_pulse_postgres_db_server.private_ip_address

  depends_on = [google_sql_database_instance.social_pulse_postgres_db_server]
}

output "bigquery_dataset_id" {
  description = "The ID of the BigQuery dataset."
  value       = google_bigquery_dataset.social_pulse_sentiment_dataset.dataset_id

  depends_on = [google_bigquery_dataset.social_pulse_sentiment_dataset]
}

output "pubsub_topic_name" {
  description = "The Pub/Sub topic name to publish to WFE Executor"
  value       = google_pubsub_topic.workflow_executor_topic.name

  depends_on = [google_pubsub_topic.workflow_executor_topic]
}
