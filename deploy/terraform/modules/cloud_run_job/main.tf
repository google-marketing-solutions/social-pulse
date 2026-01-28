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

  depends_on = [null_resource.job_dep]
}

resource "null_resource" "wait_for_image" {
  provisioner "local-exec" {
    command = <<EOT
#!/usr/bin/env bash
set -e
IMAGE="${var.image}"
PROJECT="${var.project_id}"
TRIES=${var.image_wait_retries}
SLEEP=${var.image_wait_sleep}
i=0
  while [ $i -lt $TRIES ]; do
  if gcloud artifacts docker images describe "$${IMAGE}" --project="$${PROJECT}" >/dev/null 2>&1; then
    echo "Image $${IMAGE} found."
    exit 0
  fi
  i=$((i+1))
  echo "Waiting for image $${IMAGE}... retry $i/$TRIES"
  sleep $SLEEP
done
echo "Image $${IMAGE} not found after $${TRIES} attempts." >&2
exit 1
EOT
  }
}

/* Make job creation wait for image */
resource "null_resource" "job_dep" {
  depends_on = [null_resource.wait_for_image]
}

