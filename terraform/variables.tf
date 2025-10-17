# Terraform Variables for ContextPilot

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  default     = "gen-lang-client-0805532064"
}

variable "region" {
  description = "Google Cloud Region"
  type        = string
  default     = "us-central1"
}

variable "backend_image" {
  description = "Docker image for backend (in GCR)"
  type        = string
  default     = "gcr.io/gen-lang-client-0805532064/contextpilot-backend:latest"
}

variable "environment" {
  description = "Environment (production, staging, development)"
  type        = string
  default     = "production"
}

variable "billing_account_id" {
  description = "Google Cloud Billing Account ID (format: XXXXXX-XXXXXX-XXXXXX)"
  type        = string
  default     = "015692-3F1860-6F330A"
}

