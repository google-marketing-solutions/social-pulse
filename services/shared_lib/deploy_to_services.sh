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

# This script automates the process of building the socialpulse-common wheel,
# calculating its hash, and updating the requirements.txt file for dependent services.

set -e

# Ensure the script is run from the services/shared_lib directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: This script must be run from the 'services/shared_lib' directory."
    exit 1
fi

echo "Building socialpulse-common wheel..."
# Clean the dist directory before building
rm -rf dist
python -m build --no-isolation

WHEEL_FILE=$(find dist -name "socialpulse_common-*.whl")
if [ -z "$WHEEL_FILE" ]; then
    echo "Error: Could not find wheel file in dist/ directory."
    exit 1
fi
echo "Successfully built wheel: $WHEEL_FILE"

NEW_HASH=$(sha256sum "$WHEEL_FILE" | awk '{print $1}')
echo "Calculated new sha256 hash: $NEW_HASH"

# Array of requirement files to update
REQUIREMENT_FILES=(
    "../analysis_service/requirements.txt"
    "../report_service/requirements.txt"
)

for REQ_FILE in "${REQUIREMENT_FILES[@]}"; do
    if [ ! -f "$REQ_FILE" ]; then
        echo "Warning: Requirements file not found, skipping: $REQ_FILE"
        continue
    fi

    echo "Updating requirements file: $REQ_FILE"

    # Use awk to replace the hashes for socialpulse-common
    awk -v new_hash="$NEW_HASH" '
        BEGIN { in_spc_block = 0 }
        /socialpulse-common/ {
            print
            printf "    --hash=sha256:%s\n", new_hash
            in_spc_block = 1
            next
        }
        in_spc_block == 1 && /^    --hash=/ {
            next
        }
        in_spc_block == 1 && !/^    --hash=/ {
            in_spc_block = 0
        }
        { print }
    ' "$REQ_FILE" > "$REQ_FILE.tmp"

    mv "$REQ_FILE.tmp" "$REQ_FILE"

    echo "Successfully updated $REQ_FILE."
done

echo ""
echo "Workflow complete."
echo "Please review and commit the changes to your Git repository."