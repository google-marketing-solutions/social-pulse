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
