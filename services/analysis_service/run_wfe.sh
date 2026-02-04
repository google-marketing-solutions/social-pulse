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

# Runs the workflow executor with the provided execution ID
# Usage: ./run_wfe.sh [execution ID]

set -e  # Exit immediately if a command exits with a non-zero status

if [ -z "$1" ]; then
  echo "Error: Execution ID not provided."
  echo "Usage: $0 [execution ID]"
  exit 1
fi

EXECUTION_ID=$1

# Ensure we are in the correct directory (optional but good practice)
SCRIPT_DIR="$(dirname "$0")"
cd "$SCRIPT_DIR"

if [ ! -d "src" ]; then
    echo "Error: 'src' directory not found in $SCRIPT_DIR"
    exit 1
fi

echo "Changing to src directory..."
cd src/

echo "Starting Workflow Executor for Execution ID: $EXECUTION_ID"
echo "Environment: APP_ENV=dev"

# Run the executor ensuring environment variables are set
# PYTHONPATH is updated to include the current directory (.)
APP_ENV=dev PYTHONPATH=.:$PYTHONPATH python3 api/workflow_executor.py "$EXECUTION_ID" || {
    echo "Error: Workflow execution failed."
    exit 1
}

echo "Workflow execution completed successfully."