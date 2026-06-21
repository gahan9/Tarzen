// SPDX-License-Identifier: MIT
// Least-privilege IAM and data-plane resources for the Carbon backend.
// Each role is the minimum needed for one capability; no project-wide
// editor/owner grants.

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Dedicated runtime service account for the Cloud Run service.
resource "google_service_account" "runtime" {
  account_id   = "carbon-api-runtime"
  display_name = "Carbon API Cloud Run runtime (least privilege)"
}

locals {
  sa_member = "serviceAccount:${google_service_account.runtime.email}"
}

# --- Least-privilege role bindings -----------------------------------------

# Firestore: read/write the app's documents only (no admin).
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = local.sa_member
}

# Vertex AI: invoke Gemini (predict), no model management.
resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = local.sa_member
}

# Secret Manager: read secret payloads only.
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = local.sa_member
}

# Pub/Sub: publish footprint events to a single topic.
resource "google_pubsub_topic" "footprint_events" {
  name = "footprint-events"
}

resource "google_pubsub_topic_iam_member" "publisher" {
  topic  = google_pubsub_topic.footprint_events.name
  role   = "roles/pubsub.publisher"
  member = local.sa_member
}

# BigQuery: dataEditor scoped to ONE analytics dataset (not the project).
resource "google_bigquery_dataset" "analytics" {
  dataset_id  = "carbon_analytics"
  location    = var.region
  description = "Aggregate-only footprint analytics (no raw user text)."
}

resource "google_bigquery_dataset_iam_member" "data_editor" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = local.sa_member
}

# --- Google Maps Distance Matrix API key (verified-ticket distance lookup) ---
#
# The key VALUE is never stored in Terraform or git: this resource creates only
# the secret container; add the payload out-of-band, e.g.
#   printf '%s' "$MAPS_KEY" | gcloud secrets versions add maps-api-key --data-file=-
# The backend reads it as MAPS_API_KEY (SecretStr) at the I/O boundary.
resource "google_secret_manager_secret" "maps_api_key" {
  secret_id = "maps-api-key"
  replication {
    auto {}
  }
}

# Per-secret accessor grant (tighter than the project-wide binding above; the
# project-level secret_accessor could be removed once every secret is granted
# individually like this).
resource "google_secret_manager_secret_iam_member" "maps_key_accessor" {
  secret_id = google_secret_manager_secret.maps_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = local.sa_member
}

# --- Memorystore (Redis) leaderboard ZSET backend ---------------------------
#
# Backs the regional/global leaderboard sorted set for multi-instance Cloud Run
# (the in-memory store only ranks within a single instance). AUTH + in-transit
# TLS are enabled; the generated AUTH string is pushed into Secret Manager so it
# never lands in env files or logs.
data "google_compute_network" "vpc" {
  name = var.network
}

resource "google_redis_instance" "leaderboard" {
  name               = "carbon-leaderboard"
  tier               = var.redis_tier
  memory_size_gb     = var.redis_memory_size_gb
  region             = var.region
  redis_version      = var.redis_version
  authorized_network = data.google_compute_network.vpc.id
  connect_mode       = "DIRECT_PEERING"
  display_name       = "Carbon leaderboard ZSET"

  auth_enabled            = true
  transit_encryption_mode = "SERVER_AUTHENTICATION"
}

# Store the Redis AUTH string in Secret Manager (least-privilege per-secret
# grant), surfaced to the backend as REDIS_PASSWORD.
resource "google_secret_manager_secret" "redis_auth" {
  secret_id = "redis-auth-string"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "redis_auth" {
  secret      = google_secret_manager_secret.redis_auth.id
  secret_data = google_redis_instance.leaderboard.auth_string
}

resource "google_secret_manager_secret_iam_member" "redis_auth_accessor" {
  secret_id = google_secret_manager_secret.redis_auth.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = local.sa_member
}

# Serverless VPC Access connector: lets Cloud Run egress into the VPC to reach
# the Memorystore private IP. Attach it to the service at deploy time
# (`gcloud run deploy --vpc-connector carbon-vpc --vpc-egress private-ranges-only`).
resource "google_vpc_access_connector" "serverless" {
  name          = "carbon-vpc"
  region        = var.region
  network       = data.google_compute_network.vpc.id
  ip_cidr_range = var.vpc_connector_cidr
}

# --- Backend env-var wiring (set on the Cloud Run service at deploy) ----------
#
# The backend's typed settings (`core/config.py`) read these. Secrets are
# injected as Secret Manager references, not plaintext env values:
#
#   MAPS_API_KEY     -> secret: ${google_secret_manager_secret.maps_api_key.secret_id}
#   REDIS_PASSWORD   -> secret: ${google_secret_manager_secret.redis_auth.secret_id}
#   REDIS_HOST       -> ${google_redis_instance.leaderboard.host}
#   REDIS_PORT       -> ${google_redis_instance.leaderboard.port}
#   REDIS_USE_TLS    -> "true"   (transit encryption is SERVER_AUTHENTICATION)
#   GEO_COUNTRY_HEADER -> e.g. "x-client-geo-country" (load-balancer geo header)
#   LEADERBOARD_TOP_N  -> e.g. "50"
#
# When REDIS_HOST is set the backend swaps InMemoryLeaderboardStore for the
# Memorystore-backed ZSET automatically (see backend/src/carbon/main.py).

output "runtime_service_account" {
  description = "Email of the least-privilege Cloud Run runtime service account."
  value       = google_service_account.runtime.email
}

output "redis_host" {
  description = "Memorystore private IP — set as REDIS_HOST on the service."
  value       = google_redis_instance.leaderboard.host
}

output "redis_port" {
  description = "Memorystore port — set as REDIS_PORT on the service."
  value       = google_redis_instance.leaderboard.port
}

output "vpc_connector_id" {
  description = "Serverless VPC connector to attach to the Cloud Run service."
  value       = google_vpc_access_connector.serverless.id
}

output "maps_api_key_secret_id" {
  description = "Secret Manager id for the Maps API key (add the value out-of-band)."
  value       = google_secret_manager_secret.maps_api_key.secret_id
}

output "redis_auth_secret_id" {
  description = "Secret Manager id holding the Redis AUTH string (REDIS_PASSWORD)."
  value       = google_secret_manager_secret.redis_auth.secret_id
}
