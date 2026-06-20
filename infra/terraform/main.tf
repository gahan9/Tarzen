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
