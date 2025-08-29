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

from tasks.ports import trigger

logger = logging.getLogger(__name__)


class HttpWorkflowExecutionTrigger(trigger.WorkflowExecutionTrigger):
  """Triggers the WFE Cloud Function by making a secure HTTP POST request."""

  def __init__(self, trigger_url: str):
    if not trigger_url:
      raise ValueError("Trigger URL cannot be empty.")
    self._trigger_url = trigger_url
    self._auth_request = google.auth.transport.requests.Request()

  def trigger_workflow(self, execution_id: str) -> None:
    """Makes an authenticated HTTP call to the WFE function."""
    logger.info("Fetching OIDC token for service-to-service authentication.")
    id_token = google.oauth2.id_token.fetch_id_token(
        self._auth_request, self._trigger_url
    )

    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json",
    }
    payload = {"execution_id": execution_id}

    logger.info(
        "Making POST request to trigger execution_id '%s' at URL: %s",
        execution_id,
        self._trigger_url,
    )
    response = requests.post(
        self._trigger_url, headers=headers, json=payload, timeout=30
    )

    response.raise_for_status()
    logger.info(
        "Successfully triggered workflow for execution_id '%s'.", execution_id
    )
