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
#  limitations under the License
"""Adapter for triggering a workflow executor via Cloud Job API call."""

import logging
import requests

from tasks.ports import trigger


logger = logging.getLogger(__name__)

# Cloud Run Job Name for the WFE Executor Job
CLOUD_RUN_JOB_NAME = "sp-analysis-wfe"


class CloudJobWorkflowExecutionTrigger(trigger.WorkflowExecutionTrigger):
  """Concrete implementation to trigger a Cloud Run Job via its REST API."""

  def __init__(self, project_id: str, region: str):
    """Initializes the trigger with configuration.

    Args:
      project_id: The Google Cloud project ID.
      region: The Google Cloud region where the Cloud Run Job is deployed.
    """
    self._project_id = project_id
    self._region = region

    # Construct the full URL for the ':run' API endpoint
    self._api_url = (
        f"https://{self._region}-run.googleapis.com/v2/projects/"
        f"{self._project_id}/locations/{self._region}/jobs/"
        f"{CLOUD_RUN_JOB_NAME}:run"
    )
    logger.info("Workflow Job API URL set to: %s", self._api_url)

  def _get_access_token(self) -> str:
    """Fetches the identity token for the Service Account."""
    try:
      # Token is provided by the metadata server
      response = requests.get(
          "http://metadata.google.internal/computeMetadata/v1/"
          "instance/service-accounts/default/token",
          headers={"Metadata-Flavor": "Google"}
      )
      response.raise_for_status()
      return response.json().get("access_token")
    except Exception:
      logger.critical(
          "FATAL: Failed to retrieve service account access token."
      )
      raise

  def trigger_workflow(self, execution_id: str) -> None:
    """Triggers the execution of the Cloud Run Job via the API.

    The execution_id is passed as a positional argument override.

    Args:
      execution_id: The ID of the workflow execution.
    """
    access_token = self._get_access_token()

    # Payload to override the job's command line arguments.
    payload = {
        "overrides": {
            "containerOverrides": [{
                # Pass ID as positional argument
                "args": [execution_id]
            }]
        }
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    logger.info(
        "Triggering Cloud Run Job execution for ID: %s", execution_id
    )

    response = requests.post(self._api_url, headers=headers, json=payload)

    try:
      response.raise_for_status()
      logger.info(
          "Successfully started Cloud Run Job Execution: %s",
          response.json().get("name", "N/A")
      )
    except requests.HTTPError as e:
      error_msg = e.response.text
      status_code = e.response.status_code
      logger.error(
          "API Call failed (Status: %s). Response: %s",
          status_code,
          error_msg
      )
      raise RuntimeError(
          f"Cloud Run Job API call failed: {error_msg}"
      ) from e
