#!/usr/bin/env bash
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Deploy script for Social Pulse.

# --- PARAMETER CHECK AND PROJECT CONFIGURATION ---
if [ -z "$1" ]; then
    echo "Error: Missing PROJECT_ID argument."
    echo "Usage: $0 <PROJECT_ID>"
    exit 1
fi

PROJECT_ID="$1"
LOCATION="us-central1" # Assuming fixed region from Terraform
ANALYSIS_MIGRATION_JOB_NAME="sp-analysis-migration-job"
REPORT_MIGRATION_JOB_NAME="sp-report-migration-job"


echo "Setting gcloud configuration project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# --- API ENABLEMENT ---
echo "Enabling required Google Cloud APIs..."

set -x
gcloud services enable aiplatform.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable eventarc.googleapis.com
gcloud services enable iam.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable servicenetworking.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable vpcaccess.googleapis.com
gcloud services enable youtube.googleapis.com
set +x

# --- SHARED LIBRARY BUILD/DEPLOYMENT AND REQUIREMENTS UPDATE ---
echo "Building shared library and updating dependent service requirements..."
cd ../services/shared_lib
./deploy_to_services.sh
cd ../../deploy

# --- TERRAFORM EXECUTION (Creates the job definition and new service revisions) ---
echo "Initializing Terraform..."
cd terraform/
terraform init

echo "Applying Terraform configuration..."
terraform apply -auto-approve

# --- MIGRATION EXECUTION ---
echo "Executing Cloud Run Job for Analysis Database Migrations..."

gcloud run jobs execute "${ANALYSIS_MIGRATION_JOB_NAME}" \
   --region="${LOCATION}" \
   --wait

if [ $? -ne 0 ]; then
   echo "Error: Database migration job failed. Halting deployment."
   exit 1
fi
echo "[Analysis] Database migration successful. Directing traffic to new revisions."


echo "Executing Cloud Run Job for Report Database Migrations..."
gcloud run jobs execute "${REPORT_MIGRATION_JOB_NAME}" \
    --region="${LOCATION}" \
    --wait

if [ $? -ne 0 ]; then
    echo "Error: Database migration job failed. Halting deployment."
    exit 1
fi
echo "[Analysis] Database migration successful. Directing traffic to new revisions."


echo "Deployment complete."
cd ..
