resource "google_cloud_run_v2_service" "default" {
  project             = var.project_id
  name                = var.service_name
  location            = var.location
  deletion_protection = var.deletion_protection

  template {
    service_account = var.service_account_email
    labels          = var.labels

    containers {
      image = var.image
      ports {
        container_port = var.port
      }

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

    scaling {
      min_instance_count = var.min_instance_count
    }
  }
}
