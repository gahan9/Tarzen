// SPDX-License-Identifier: MIT
// Input variables for the Carbon backend infrastructure.

variable "project_id" {
  type        = string
  description = "Target Google Cloud project id."
}

variable "region" {
  type        = string
  description = "Region for Cloud Run, Pub/Sub, and BigQuery resources."
  default     = "us-central1"
}
