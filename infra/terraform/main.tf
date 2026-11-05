locals {
  apis = toset([
    "artifactregistry.googleapis.com",
    "billingbudgets.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "cloudtrace.googleapis.com",
    "firebase.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "identitytoolkit.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
    "sts.googleapis.com",
  ])

  # Secret Manager secret ID => environment variable. Values are added out of band (gcloud), never here.
  secrets = {
    "gemini-api-key"      = "GEMINI_API_KEY"
    "database-url"        = "DATABASE_URL"
    "redis-url"           = "REDIS_URL"
    "unsplash-access-key" = "UNSPLASH_ACCESS_KEY"
    "ors-api-key"         = "ORS_API_KEY"
    "sentry-dsn"          = "SENTRY_DSN"
  }
  wired_secrets = { for id in var.wired_secrets : id => local.secrets[id] }

  firebase_project = coalesce(var.firebase_project_id, var.project_id)
  documents_bucket = "${var.project_id}-travya-documents"
  image_repository = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"

  # Shared by the API service and the migrate job (Settings validates the same fields in both).
  plain_env = {
    ENVIRONMENT         = "production"
    LOG_JSON            = "true"
    FIREBASE_PROJECT_ID = local.firebase_project
    GEMINI_MODEL        = var.gemini_model
    STORAGE_BACKEND     = "gcs"
    GCS_BUCKET          = google_storage_bucket.documents.name
    FRONTEND_ORIGINS    = jsonencode(var.frontend_origins)
  }
}

data "google_project" "this" {
  project_id = var.project_id
}

resource "google_project_service" "apis" {
  for_each = local.apis

  service            = each.value
  disable_on_destroy = false
}

# ---------------------------------------------------------------------------
# Artifact Registry: one Docker repo, only the newest images kept (free tier: 0.5 GB).

resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = "travya"
  format        = "DOCKER"
  description   = "Travya container images"

  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "keep-most-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = var.artifact_keep_count
    }
  }

  cleanup_policies {
    id     = "delete-everything-else"
    action = "DELETE"
    condition {
      tag_state = "ANY"
    }
  }

  depends_on = [google_project_service.apis]
}

# ---------------------------------------------------------------------------
# Runtime identity of the API and the migrate job.

resource "google_service_account" "runtime" {
  account_id   = "travya-runtime"
  display_name = "Travya API runtime"
  description  = "Identity of the travya-api service and the travya-migrate job"

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "runtime_trace" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = google_service_account.runtime.member
}

# Signed URLs for trip documents: the runtime SA signs blobs as itself through the IAM Credentials API.
resource "google_service_account_iam_member" "runtime_self_token_creator" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = google_service_account.runtime.member
}

# ---------------------------------------------------------------------------
# Secrets (containers only; add versions with `gcloud secrets versions add <id> --data-file=-`).

resource "google_secret_manager_secret" "app" {
  for_each = local.secrets

  secret_id = each.key

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_iam_member" "runtime" {
  for_each = google_secret_manager_secret.app

  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.runtime.member
}

# ---------------------------------------------------------------------------
# Trip documents bucket: private, regional (free tier), deleted after a year.

resource "google_storage_bucket" "documents" {
  name          = local.documents_bucket
  location      = upper(var.region)
  storage_class = "STANDARD"

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  # Soft-deleted objects are billed; nothing here needs a recycle bin.
  soft_delete_policy {
    retention_duration_seconds = 0
  }

  lifecycle_rule {
    condition {
      age = var.documents_retention_days
    }
    action {
      type = "Delete"
    }
  }

  # Browsers upload and download through signed URLs.
  cors {
    origin          = var.frontend_origins
    method          = ["GET", "HEAD"]
    response_header = ["Content-Type", "Content-Disposition", "Content-Length"]
    max_age_seconds = 3600
  }

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "runtime_documents" {
  bucket = google_storage_bucket.documents.name
  role   = "roles/storage.objectAdmin"
  member = google_service_account.runtime.member
}

# ---------------------------------------------------------------------------
# Cloud Run: the API (scale to zero, one instance at most) and the migration job.
# Deploys only swap the image (deploy.yml), so Terraform ignores image changes.

resource "google_cloud_run_v2_service" "api" {
  name                = "travya-api"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = var.deletion_protection

  template {
    service_account                  = google_service_account.runtime.email
    timeout                          = "300s"
    max_instance_request_concurrency = 40

    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }

    containers {
      image = var.api_image

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      dynamic "env" {
        for_each = local.plain_env
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.wired_secrets
        content {
          name = env.value
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.app[env.key].secret_id
              version = "latest"
            }
          }
        }
      }

      startup_probe {
        http_get {
          path = "/api/v1/health/live"
        }
        period_seconds    = 3
        timeout_seconds   = 2
        failure_threshold = 20
      }

      liveness_probe {
        http_get {
          path = "/api/v1/health/live"
        }
        period_seconds    = 30
        timeout_seconds   = 3
        failure_threshold = 3
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  lifecycle {
    ignore_changes = [
      client,
      client_version,
      template[0].containers[0].image,
    ]
  }

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_iam_member.runtime,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.api.name
  location = google_cloud_run_v2_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_job" "migrate" {
  name                = "travya-migrate"
  location            = var.region
  deletion_protection = var.deletion_protection

  template {
    task_count  = 1
    parallelism = 1

    template {
      service_account = google_service_account.runtime.email
      timeout         = "600s"
      max_retries     = 0

      containers {
        image   = var.api_image
        command = ["alembic"]
        args    = ["upgrade", "head"]

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }

        dynamic "env" {
          for_each = local.plain_env
          content {
            name  = env.key
            value = env.value
          }
        }

        dynamic "env" {
          for_each = local.wired_secrets
          content {
            name = env.value
            value_source {
              secret_key_ref {
                secret  = google_secret_manager_secret.app[env.key].secret_id
                version = "latest"
              }
            }
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      client,
      client_version,
      template[0].template[0].containers[0].image,
    ]
  }

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_iam_member.runtime,
  ]
}

# ---------------------------------------------------------------------------
# GitHub Actions deployer: Workload Identity Federation, no JSON keys.
# (The gh-oidc module from terraform-google-modules pins google < 8, so the three resources are inline.)

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"
  description               = "OIDC tokens from GitHub Actions"

  depends_on = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "travya-deploy"
  display_name                       = "Travya deploys from main"

  attribute_mapping = {
    "google.subject"             = "assertion.sub"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_id"    = "assertion.repository_id"
    "attribute.repository_owner" = "assertion.repository_owner"
    "attribute.ref"              = "assertion.ref"
  }

  # Tokens from any other repository or branch are rejected before any IAM check.
  attribute_condition = "assertion.repository == \"${var.github_repository}\" && assertion.ref == \"${var.github_ref}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "deployer" {
  account_id   = "travya-deployer"
  display_name = "Travya GitHub deployer"
  description  = "Impersonated by GitHub Actions (main) to push images and deploy Cloud Run"

  depends_on = [google_project_service.apis]
}

resource "google_service_account_iam_member" "deployer_wif" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}"
}

# Push images to the one repository.
resource "google_artifact_registry_repository_iam_member" "deployer_writer" {
  location   = google_artifact_registry_repository.images.location
  repository = google_artifact_registry_repository.images.name
  role       = "roles/artifactregistry.writer"
  member     = google_service_account.deployer.member
}

# Update the service and the job, run job executions. No IAM-policy or project-admin rights.
resource "google_project_iam_member" "deployer_run" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = google_service_account.deployer.member
}

# Deploy revisions that run as the runtime SA (actAs on that SA only).
resource "google_service_account_iam_member" "deployer_act_as_runtime" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = google_service_account.deployer.member
}

# ---------------------------------------------------------------------------
# Budget alert: e-mails the billing admins at 50, 90 and 100% of a $1 monthly budget.

resource "google_billing_budget" "monthly" {
  billing_account = var.billing_account_id
  display_name    = "travya-monthly"

  budget_filter {
    projects        = ["projects/${data.google_project.this.number}"]
    calendar_period = "MONTH"
  }

  amount {
    specified_amount {
      currency_code = var.budget_currency_code
      units         = tostring(var.budget_amount)
    }
  }

  threshold_rules {
    threshold_percent = 0.5
  }
  threshold_rules {
    threshold_percent = 0.9
  }
  threshold_rules {
    threshold_percent = 1.0
  }

  depends_on = [google_project_service.apis]
}
