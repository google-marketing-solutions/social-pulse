#!/bin/bash

#  Copyright 2025 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# Copyright 2025 Google LLC
#
# Script to build and publish socialpulse-common to Artifact Registry
# and update service requirements.txt files.

set -e

REPO_URL="$1"

if [ -z "$REPO_URL" ]; then
    echo "Error: REPO_URL argument is required."
    echo "Usage: $0 <REPO_URL>"
    exit 1
fi

# Ensure we are in the script's directory
cd "$(dirname "$0")"

echo "Building socialpulse-common wheel..."
# Clean dist directory
rm -rf dist
python3 -m build

WHEEL_FILE=$(find dist -name "socialpulse_common-*.whl")
if [ -z "$WHEEL_FILE" ]; then
    echo "Error: Could not find wheel file in dist/ directory."
    exit 1
fi
echo "Successfully built: $WHEEL_FILE"

# Extract package name and version from wheel filename
PACKAGE_NAME=$(basename "$WHEEL_FILE" | cut -d- -f1 | sed 's/_/-/g')
PACKAGE_VERSION=$(basename "$WHEEL_FILE" | cut -d- -f2)

echo "Detected package: $PACKAGE_NAME version: $PACKAGE_VERSION"

echo "Checking if version $PACKAGE_VERSION already exists..."
if gcloud artifacts versions describe "$PACKAGE_VERSION" \
    --package="$PACKAGE_NAME" \
    --repository="sp-python-repo" \
    --location="us-central1" \
    --project="${PROJECT_ID:-$(gcloud config get-value project)}" > /dev/null 2>&1; then

    echo "Version $PACKAGE_VERSION exists. Deleting..."
    gcloud artifacts versions delete "$PACKAGE_VERSION" \
        --package="$PACKAGE_NAME" \
        --repository="sp-python-repo" \
        --location="us-central1" \
        --project="${PROJECT_ID:-$(gcloud config get-value project)}" \
        --quiet
    echo "Version $PACKAGE_VERSION deleted."
else
    echo "Version $PACKAGE_VERSION does not exist. Proceeding with upload."
fi

echo "Uploading to Artifact Registry: $REPO_URL"
# Use twine to upload. Assumes keyring is configured or gcloud auth is active.
python3 -m twine upload --repository-url "$REPO_URL" "$WHEEL_FILE"

NEW_HASH=$(sha256sum "$WHEEL_FILE" | awk '{print $1}')
echo "Calculated hash: $NEW_HASH"

# Array of requirement files to update
REQUIREMENT_FILES=(
    "../analysis_service/requirements.txt"
    "../report_service/requirements.txt"
)

for REQ_FILE in "${REQUIREMENT_FILES[@]}"; do
    ./scripts/update_requirements_hash.sh "$NEW_HASH" "$REQ_FILE"
done

echo "Build and publish complete."
