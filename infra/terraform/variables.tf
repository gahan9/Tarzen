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

# --- Leaderboard Memorystore (Redis) -----------------------------------------

variable "network" {
  type        = string
  description = <<-EOT
    Self-link or name of the VPC network authorized to reach the Memorystore
    instance and host the Serverless VPC Access connector. Cloud Run egresses
    through the connector into this network to reach Redis over a private IP.
  EOT
  default     = "default"
}

variable "redis_memory_size_gb" {
  type        = number
  description = "Memorystore capacity in GB (1 GB is ample for a leaderboard ZSET)."
  default     = 1
}

variable "redis_tier" {
  type        = string
  description = "Memorystore service tier: BASIC (single node) or STANDARD_HA."
  default     = "BASIC"

  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], var.redis_tier)
    error_message = "redis_tier must be BASIC or STANDARD_HA."
  }
}

variable "redis_version" {
  type        = string
  description = "Memorystore Redis engine version."
  default     = "REDIS_7_0"
}

variable "vpc_connector_cidr" {
  type        = string
  description = <<-EOT
    Unused /28 CIDR for the Serverless VPC Access connector. Must not overlap
    any existing subnet in the network.
  EOT
  default     = "10.8.0.0/28"
}
