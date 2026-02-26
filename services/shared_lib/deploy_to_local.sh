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
# Deploy script for local development.
# Builds socialpulse-common, starts/uses a local pypiserver, and updates requirements.

set -e

# Configuration
PACKAGES_DIR="$HOME/projects/social_pulse/packages"
PORT=3322
PYPISERVER_VENV="$HOME/projects/social_pulse/.venv.pypiserver"

# Ensure we are in the script's directory
cd "$(dirname "$0")"

echo "=== Local Deployment Start ==="

# 1. Setup pypiserver environment if needed
if [ ! -d "$PYPISERVER_VENV" ]; then
    echo "Creating pypiserver virtual environment..."
    python3 -m venv "$PYPISERVER_VENV"
    "$PYPISERVER_VENV/bin/pip" install pypiserver passlib build
fi

# 2. Build the package
echo "Building socialpulse-common wheel..."
rm -rf dist
# We need 'build' installed in the user env or use the venv we just made
# Let's use the venv we just made to be safe/consistent
"$PYPISERVER_VENV/bin/python3" -m build

WHEEL_FILE=$(find dist -name "socialpulse_common-*.whl")
if [ -z "$WHEEL_FILE" ]; then
    echo "Error: Could not find wheel file in dist/ directory."
    exit 1
fi
echo "Successfully built: $WHEEL_FILE"

# 3. Setup local packages directory
mkdir -p "$PACKAGES_DIR"

# 4. Start pypiserver if not running
if ! pgrep -f "pypi-server" > /dev/null; then
    echo "Starting local pypiserver on port $PORT..."
    nohup "$PYPISERVER_VENV/bin/pypi-server" run -p $PORT -a . -P . "$PACKAGES_DIR" > "$PACKAGES_DIR/pypiserver.log" 2>&1 &
    # Give it a moment to start
    sleep 2
    echo "pypiserver started."
else
    echo "pypiserver is already running."
fi

# 5. Copy package to local repo
echo "Deploying to local packages directory: $PACKAGES_DIR"
cp "$WHEEL_FILE" "$PACKAGES_DIR/"

# 6. Calculate Hash
NEW_HASH=$(sha256sum "$WHEEL_FILE" | awk '{print $1}')
echo "Calculated hash: $NEW_HASH"

# 7. Update requirements files
# Array of requirement files to update
REQUIREMENT_FILES=(
    "../analysis_service/requirements.txt"
    "../report_service/requirements.txt"
)

for REQ_FILE in "${REQUIREMENT_FILES[@]}"; do
    ./scripts/update_requirements_hash.sh "$NEW_HASH" "$REQ_FILE"
done

echo "=== Local Deployment Complete ==="
echo "You can now install using:"
echo "pip install \\"
echo "  --force-reinstall \\"
echo "  --no-deps \\"
echo "  --extra-index-url http://localhost:3322/simple \\"
echo "  --trusted-host localhost \\"
echo "  socialpulse-common"
