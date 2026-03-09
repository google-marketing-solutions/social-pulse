variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "location" {
  description = "The GCP region for the job."
  type        = string
}

variable "job_name" {
  description = "The name of the Cloud Run job."
  type        = string
}

variable "image" {
  description = "The container image to deploy."
  type        = string
}

variable "service_account_email" {
  description = "The email of the service account for the Cloud Run job."
  type        = string
}

variable "command" {
  description = "The command to run in the container."
  type        = list(string)
  default     = null
}

variable "args" {
  description = "The arguments to pass to the command."
  type        = list(string)
  default     = null
}

variable "env_vars" {
  description = "A map of environment variables to set in the container."
  type        = map(string)
  default     = {}
}

variable "secret_env_vars" {
  description = "A map of environment variables to set from Secret Manager. Key is env var name, value is secret ID."
  type        = map(string)
  default     = {}
}

variable "vpc_connector_id" {
  description = "The ID of the VPC Access Connector."
  type        = string
}

variable "labels" {
  description = "A map of labels to apply to the job."
  type        = map(string)
  default     = {}
}

variable "max_retries" {
  description = "The maximum number of retries for the job."
  type        = number
  default     = 3
}

variable "timeout" {
  description = "The timeout for the job execution."
  type        = string
  default     = "600s"
}

variable "deletion_protection" {
  description = "Whether to enable deletion protection for the job."
  type        = bool
  default     = false
}

variable "image_wait_retries" {
  description = "How many times to poll Artifact Registry for the image before failing."
  type        = number
  default     = 30
}

variable "image_wait_sleep" {
  description = "Seconds to sleep between image existence polls."
  type        = number
  default     = 5
}

variable "cpu" {
  description = "The number of CPUs to allocate for the container."
  type        = string
  default     = "1"
}

variable "memory" {
  description = "The amount of memory to allocate for the container."
  type        = string
  default     = "512Mi"
}
