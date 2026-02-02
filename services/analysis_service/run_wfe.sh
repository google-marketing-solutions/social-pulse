#!/bin/bash
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