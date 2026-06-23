terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

# Cloud SQL
resource "google_sql_database_instance" "main" {
  name             = "enterprise-ai-sql"
  database_version = "POSTGRES_16"
  region           = var.region
  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled = true
    }
  }
  deletion_protection = false
}

resource "google_sql_database" "db" {
  name     = "enterprise_ai"
  instance = google_sql_database_instance.main.name
}

# Cloud Storage
resource "google_storage_bucket" "rag" {
  name          = "${var.project_id}-enterprise-rag"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}

# BigQuery dataset
resource "google_bigquery_dataset" "analytics" {
  dataset_id = "enterprise_analytics"
  location   = var.region
}

resource "google_bigquery_table" "incidents" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  table_id   = "incidents"
  schema     = jsonencode([
    { name = "title", type = "STRING" },
    { name = "severity", type = "STRING" },
    { name = "status", type = "STRING" },
    { name = "created_at", type = "TIMESTAMP" },
  ])
}

# Artifact Registry
resource "google_artifact_registry_repository" "services" {
  location      = var.region
  repository_id = "enterprise-ai"
  format        = "DOCKER"
}

locals {
  services = {
    ai-gateway         = { port = 8080, module = "cloud_run_services.ai_gateway.main" }
    rag-service        = { port = 8081, module = "cloud_run_services.rag_service.main" }
    agent-service      = { port = 8082, module = "cloud_run_services.agent_service.main" }
    jira-service       = { port = 8083, module = "cloud_run_services.jira_service.main" }
    confluence-service = { port = 8084, module = "cloud_run_services.confluence_service.main" }
    github-service     = { port = 8085, module = "cloud_run_services.github_service.main" }
    reporting-service  = { port = 8086, module = "cloud_run_services.reporting_service.main" }
  }
}

resource "google_cloud_run_v2_service" "services" {
  for_each = local.services

  name     = each.key
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
  containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/enterprise-ai/${each.key}:latest"
      ports {
        container_port = each.value.port
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "USE_VERTEX_AI"
        value = "true"
      }
      env {
        name  = "GCS_BUCKET"
        value = google_storage_bucket.rag.name
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = google_bigquery_dataset.analytics.dataset_id
      }
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  for_each = google_cloud_run_v2_service.services

  name     = each.value.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "gateway_url" {
  value = google_cloud_run_v2_service.services["ai-gateway"].uri
}

output "gcs_bucket" {
  value = google_storage_bucket.rag.name
}

output "cloud_sql_connection" {
  value = google_sql_database_instance.main.connection_name
}
