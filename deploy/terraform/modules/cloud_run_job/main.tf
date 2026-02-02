resource "google_cloud_run_v2_job" "default" {
  project             = var.project_id
  name                = var.job_name
  location            = var.location
  deletion_protection = var.deletion_protection

  template {
    labels = var.labels
    template {
      service_account = var.service_account_email
      max_retries     = var.max_retries
      timeout         = var.timeout

      containers {
        image   = var.image
        command = var.command
        args    = var.args

        dynamic "env" {
          for_each = var.env_vars
          content {
            name  = env.key
            value = env.value
          }
        }

        dynamic "env" {
          for_each = var.secret_env_vars
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = env.value
                version = "latest"
              }
            }
          }
        }
      }

      vpc_access {
        connector = var.vpc_connector_id
        egress    = "ALL_TRAFFIC"
      }
    }
  }
}
