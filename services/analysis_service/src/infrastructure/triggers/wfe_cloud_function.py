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
"""Adapter for triggering a workflow executor via an authenticated HTTP call."""

import logging

import google.auth.transport.requests
import google.oauth2.id_token
import requests
from socialpulse_common.messages import sentiment_report as report_msg
from tasks.ports import trigger


logger = logging.getLogger(__name__)


class HttpReportStatusUpdatingService(trigger.ReportStatusUpdatingService):
  """Uses HTTP calls to update the status of a report."""

  def __init__(self, report_api_url):
    self._auth_request = google.auth.transport.requests.Request()
    self._report_api_url = report_api_url

  def mark_report_completed(
      self, report_id: str, datasets: list[report_msg.SentimentReportDataset]
  ) -> None:
    """Marks a report as completed."""
    payload = [d.model_dump() for d in datasets]
    self._send_status_update_request(
        report_id=report_id, action="mark_as_completed", payload=payload
    )

  def mark_report_in_progress(self, report_id: str) -> None:
    """Marks a report as in progress."""
    self._send_status_update_request(
        report_id=report_id, action="mark_as_in_progress"
    )

  def _build_report_service_url(self, report_id: str, action: str) -> str:
    """Builds the URL for the report completion service Cloud Function.

    Args:
      report_id: The ID of the report.
      action: The action to perform (e.g., 'mark_as_completed').
    Returns:
      The URL for the report completion service Cloud Function.
    """
    return f"{self._report_api_url}/api/{report_id}/{action}"

  def _send_status_update_request(
      self,
      report_id: str,
      action: str,
      payload: list[dict[str, any]] | None = None
  ) -> None:
    """Sends an authenticated POST request to the report service.

    Args:
      report_id: The ID of the report.
      action: The action to perform (e.g., 'mark_as_completed').
      payload: Optional JSON payload for the request.
    """
    trigger_url = self._build_report_service_url(report_id, action)
    id_token = google.oauth2.id_token.fetch_id_token(
        self._auth_request, trigger_url
    )

    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json",
    }

    action_desc = action.replace("_", " ")
    logger.info(
        "Making POST request to %s report '%s' at URL: %s",
        action_desc,
        report_id,
        trigger_url,
    )
    response = requests.post(
        trigger_url, headers=headers, json=payload, timeout=30
    )

    if not response.ok:
      logger.error(
          "Request to %s failed with status code %s. Response body: %s",
          trigger_url,
          response.status_code,
          response.text,
      )

    response.raise_for_status()
    logger.info("Successfully performed action '%s' for report '%s'.",
                action_desc, report_id)
