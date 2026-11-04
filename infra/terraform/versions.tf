terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.10"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region

  # Billing budgets (and a few other APIs) need a quota project when called with user credentials.
  user_project_override = true
  billing_project       = var.project_id

  default_labels = {
    app        = "travya"
    managed-by = "terraform"
  }
}
