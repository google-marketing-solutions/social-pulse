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
"""Module for implementations of the WFE executor using HTTP endpoints."""
import logging

from domain.ports import api
import requests
from socialpulse_common import config
from socialpulse_common.messages import sentiment_report


logger = logging.getLogger(__name__)


HTTP_ENDPOINT_SERVER_PATH = "api/run_report"


class HttpEndpoingWorkflowExecutionService(api.WorkflowExecutionService):
  """Implementation of the WFE executor using HTTP endpoints."""

  def __init__(self, workflow_runner_api_url: str) -> None:
    self._workflow_runner_api_url = workflow_runner_api_url

  def trigger_run_report(self, report: sentiment_report.SentimentReport):
    """Triggers the workflow for generating a sentiment report.

    Args:
      report: The sentiment report to generate.
    """
    try:
      complete_url = (
          f"{self._workflow_runner_api_url}/{HTTP_ENDPOINT_SERVER_PATH}"
      )
      logger.info("Sending run report request to: %s", complete_url)

      response = requests.post(
          complete_url,
          headers=self._generate_request_headers(),
          json=report.model_dump(mode="json"),
      )

      response.raise_for_status()
      logger.info(
          "Successfully started Cloud Run Job Execution: %s",
          response.json().get("name", "N/A"),
      )

    except requests.HTTPError as e:
      error_msg = e.response.text
      status_code = e.response.status_code
      loggable_error = (
          "API Call failed (Status: %s). Response: %s",
          status_code,
          error_msg,
      )
      logger.error(loggable_error)
      raise RuntimeError(loggable_error) from e

    except Exception as e:
      loggable_error = ("API Call failed: %s", str(e))
      logger.error(loggable_error)
      raise RuntimeError(loggable_error) from e

  def _generate_request_headers(self):
    headers = {"Content-Type": "application/json"}

    if not config.is_development():
      id_token = self._get_identity_token(
          audience=self._workflow_runner_api_url
      )
      headers.update({"Authorization": f"Bearer {id_token}"})

    return headers

  def _get_identity_token(self, audience: str) -> str:
    """Fetches the OIDC Identity token for Cloud Run invocation."""
    try:
      metadata_url = (
          "http://metadata.google.internal/computeMetadata/v1/"
          "instance/service-accounts/default/identity"
      )

      response = requests.get(
          metadata_url,
          params={"audience": audience},
          headers={"Metadata-Flavor": "Google"},
      )
      response.raise_for_status()

      # Important: The identity endpoint returns the token as raw text,
      # not inside a JSON object like the access token endpoint.
      return response.text.strip()

    except Exception:
      logger.critical(
          "FATAL: Failed to retrieve service account identity token."
      )
      raise
