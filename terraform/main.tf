# ContextPilot - Terraform Infrastructure as Code
# Deploys complete Google Cloud infrastructure for ContextPilot

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  # Backend for state storage (optional - uncomment for production)
  # backend "gcs" {
  #   bucket = "contextpilot-terraform-state"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "containerregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "pubsub.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
  ])
  
  service            = each.value
  disable_on_destroy = false
}

# Pub/Sub Topics for Event Bus
resource "google_pubsub_topic" "event_topics" {
  for_each = toset([
    "git-events",
    "proposal-events",
    "context-events",
    "spec-events",
    "strategy-events",
    "milestone-events",
    "coach-events",
    "retrospective-events",
    "artifact-events",
    "reward-events",
    "dead-letter-queue",
  ])
  
  name = each.value
  
  depends_on = [google_project_service.required_apis]
}

# Pub/Sub Subscriptions for Agents
resource "google_pubsub_subscription" "agent_subscriptions" {
  for_each = {
    spec-agent         = "spec-events"
    git-agent          = "git-events"
    strategy-agent     = "strategy-events"
    coach-agent        = "coach-events"
    retrospective-agent = "retrospective-events"
  }
  
  name  = "${each.key}-sub"
  topic = google_pubsub_topic.event_topics[each.value].name
  
  ack_deadline_seconds = 20
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.event_topics["dead-letter-queue"].id
    max_delivery_attempts = 5
  }
}

# Secret Manager for API Keys
resource "google_secret_manager_secret" "google_api_key" {
  secret_id = "GOOGLE_API_KEY"
  
  replication {
    user_managed {
      replicas {
        location = "us-central1"
      }
    }
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret" "github_token" {
  secret_id = "GITHUB_TOKEN"
  
  replication {
    user_managed {
      replicas {
        location = "us-central1"
      }
    }
  }
  
  depends_on = [google_project_service.required_apis]
}

# Grant Cloud Run access to secrets
resource "google_secret_manager_secret_iam_member" "cloud_run_secret_access" {
  secret_id = google_secret_manager_secret.google_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

resource "google_secret_manager_secret_iam_member" "cloud_run_github_token_access" {
  secret_id = google_secret_manager_secret.github_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Firestore Database
resource "google_firestore_database" "database" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  
  depends_on = [google_project_service.required_apis]
}

# Cloud Run Service
resource "google_cloud_run_service" "backend" {
  name     = "contextpilot-backend"
  location = var.region
  
  template {
    spec {
      containers {
        image = var.backend_image
        
        ports {
          container_port = 8080
        }
        
        env {
          name  = "USE_PUBSUB"
          value = "true"
        }
        
        env {
          name  = "FIRESTORE_ENABLED"
          value = "true"
        }
        
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "ENVIRONMENT"
          value = "production"
        }
        
        env {
          name  = "CONTEXTPILOT_AUTO_APPROVE_PROPOSALS"
          value = "true"
        }
        
        env {
          name = "GOOGLE_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.google_api_key.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "GITHUB_TOKEN"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.github_token.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name  = "GITHUB_REPO"
          value = "fsegall/google-context-pilot"
        }
        
        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }
      
      container_concurrency = 80
      timeout_seconds       = 300
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "autoscaling.knative.dev/minScale" = "0"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_secret_manager_secret_iam_member.cloud_run_secret_access,
  ]
}

# Make Cloud Run service public
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Data source for project info
data "google_project" "project" {
  project_id = var.project_id
}

