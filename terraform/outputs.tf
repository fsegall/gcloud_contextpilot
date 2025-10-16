# Terraform Outputs for ContextPilot

output "cloud_run_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_service.backend.status[0].url
}

output "project_id" {
  description = "Google Cloud Project ID"
  value       = var.project_id
}

output "region" {
  description = "Google Cloud Region"
  value       = var.region
}

output "pubsub_topics" {
  description = "List of Pub/Sub topics created"
  value       = [for topic in google_pubsub_topic.event_topics : topic.name]
}

output "pubsub_subscriptions" {
  description = "List of Pub/Sub subscriptions created"
  value       = [for sub in google_pubsub_subscription.agent_subscriptions : sub.name]
}

output "firestore_database" {
  description = "Firestore database name"
  value       = google_firestore_database.database.name
}

output "secret_manager_secrets" {
  description = "List of secrets in Secret Manager"
  value       = [
    google_secret_manager_secret.google_api_key.secret_id,
    google_secret_manager_secret.github_token.secret_id
  ]
}

