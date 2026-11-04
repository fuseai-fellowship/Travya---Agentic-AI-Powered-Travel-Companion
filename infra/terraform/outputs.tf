output "github_variables" {
  description = "Repository (or `production` environment) variables for .github/workflows/deploy.yml."
  value = {
    GCP_PROJECT_ID            = var.project_id
    GCP_REGION                = var.region
    WIF_PROVIDER              = google_iam_workload_identity_pool_provider.github.name
    DEPLOY_SA                 = google_service_account.deployer.email
    VITE_API_URL              = google_cloud_run_v2_service.api.uri
    VITE_FIREBASE_PROJECT_ID  = local.firebase_project
    VITE_FIREBASE_AUTH_DOMAIN = "${local.firebase_project}.firebaseapp.com"
  }
}

output "api_url" {
  description = "Public URL of the travya-api service."
  value       = google_cloud_run_v2_service.api.uri
}

output "image_repository" {
  description = "Artifact Registry path that deploy.yml pushes to (<repo>/api:<git sha>)."
  value       = local.image_repository
}

output "documents_bucket" {
  description = "GCS bucket for trip documents (GCS_BUCKET)."
  value       = google_storage_bucket.documents.name
}

output "runtime_service_account" {
  description = "Service account the API and the migrate job run as."
  value       = google_service_account.runtime.email
}

output "secrets_to_populate" {
  description = "Add a version to each before the first full apply: printf %s \"$VALUE\" | gcloud secrets versions add <id> --data-file=-"
  value       = sort(keys(local.wired_secrets))
}
