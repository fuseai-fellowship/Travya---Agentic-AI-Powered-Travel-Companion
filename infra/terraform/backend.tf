# State lives in a GCS bucket created once by hand (see terraform.tfvars.example):
#   terraform init -backend-config="bucket=<project-id>-tfstate"
terraform {
  backend "gcs" {
    prefix = "travya/production"
  }
}
