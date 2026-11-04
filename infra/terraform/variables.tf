variable "project_id" {
  description = "Google Cloud project ID (also the Firebase project unless firebase_project_id is set)."
  type        = string
}

variable "region" {
  description = "Region for Cloud Run, Artifact Registry and the documents bucket. us-central1 keeps storage in the free tier."
  type        = string
  default     = "us-central1"
}

variable "billing_account_id" {
  description = "Billing account the project is linked to (XXXXXX-XXXXXX-XXXXXX), used for the budget alert."
  type        = string
}

variable "budget_amount" {
  description = "Monthly budget that triggers the 50/90/100% alerts, in budget_currency_code units."
  type        = number
  default     = 1
}

variable "budget_currency_code" {
  description = "Currency of the billing account (the budget must use it)."
  type        = string
  default     = "USD"
}

variable "github_repository" {
  description = "owner/name of the only GitHub repository allowed to deploy."
  type        = string
  default     = "fuseai-fellowship/Travya---Agentic-AI-Powered-Travel-Companion"
}

variable "github_ref" {
  description = "Only workflows running on this ref may impersonate the deployer."
  type        = string
  default     = "refs/heads/main"
}

variable "frontend_origins" {
  description = "Browser origins of the web app (CORS on the API and on the documents bucket)."
  type        = list(string)
  default     = ["https://travya.pages.dev"]
}

variable "api_image" {
  description = "Image used when the service and job are first created. Deploys replace it; Terraform ignores later changes."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "firebase_project_id" {
  description = "Firebase project that issues ID tokens. Defaults to project_id."
  type        = string
  default     = null
}

variable "gemini_model" {
  description = "GEMINI_MODEL for the API."
  type        = string
  default     = "gemini-flash-latest"
}

variable "wired_secrets" {
  description = <<-EOT
    Secret Manager secrets mounted as env vars on the service and the migrate job. Every listed secret
    needs at least one version before the first full apply (Cloud Run rejects empty secrets), so drop
    optional ones (sentry-dsn, unsplash-access-key, ors-api-key) until they have a value.
  EOT
  type        = list(string)
  default     = ["gemini-api-key", "database-url", "redis-url", "unsplash-access-key", "ors-api-key", "sentry-dsn"]

  validation {
    condition = alltrue([
      for s in var.wired_secrets : contains(["gemini-api-key", "database-url", "redis-url", "unsplash-access-key", "ors-api-key", "sentry-dsn"], s)
    ])
    error_message = "wired_secrets may only contain gemini-api-key, database-url, redis-url, unsplash-access-key, ors-api-key and sentry-dsn."
  }
}

variable "artifact_keep_count" {
  description = "Image versions kept in Artifact Registry (the free tier is 0.5 GB)."
  type        = number
  default     = 2
}

variable "documents_retention_days" {
  description = "Trip documents are deleted this many days after upload."
  type        = number
  default     = 365
}

variable "deletion_protection" {
  description = "Protect the Cloud Run service and job from terraform destroy."
  type        = bool
  default     = true
}
