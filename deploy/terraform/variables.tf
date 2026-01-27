# variables.tf
variable "project_id" {
  description = "The ID of the GCP project to create or use."
  type        = string
}

variable "project_number" {
  description = "The project number of the GCP project to create or use."
  type        = string
}

variable "region" {
  description = "The GCP region for deploying resources."
  type        = string
  default     = "us-central1"
}

variable "bq_dataset_name" {
  description = "Name of the BQ dataset to store sentiment data created by the analysis."
  type        = string
  default     = "sentiment_analysis"
}

variable "create_new_project" {
  description = "Set to true to create a new GCP project, false to use an existing one."
  type        = bool
  default     = false
}

variable "org_id" {
  description = "The organization ID if creating a new project. Required if create_new_project is true."
  type        = string
  default     = null
}

variable "billing_account_id" {
  description = "The billing account ID if creating a new project. Required if create_new_project is true."
  type        = string
  default     = null
}

variable "db_username" {
  description = "The username for the PostgreSQL database."
  type        = string
  sensitive   = true # Marks the variable as sensitive, redacting it from logs.
}

variable "db_password" {
  description = "The password for the PostgreSQL database."
  type        = string
  sensitive   = true # Marks the variable as sensitive.
}

variable "yt_api_key" {
  description = "The YouTube API key"
  type        = string
  sensitive   = true # Marks the variable as sensitive.
}
