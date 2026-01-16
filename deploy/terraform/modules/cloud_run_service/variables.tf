variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "location" {
  description = "The GCP region for the service."
  type        = string
}

variable "service_name" {
  description = "The name of the Cloud Run service."
  type        = string
}

variable "image" {
  description = "The container image to deploy."
  type        = string
}

variable "service_account_email" {
  description = "The email of the service account for the Cloud Run service."
  type        = string
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

variable "port" {
  description = "The port the container listens on."
  type        = number
  default     = 8080
}

variable "labels" {
  description = "A map of labels to apply to the service."
  type        = map(string)
  default     = {}
}

variable "deletion_protection" {
  description = "Whether to enable deletion protection for the service."
  type        = bool
  default     = false
}
