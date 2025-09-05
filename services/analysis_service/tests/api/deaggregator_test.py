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
"""Unit tests for the DeaggregatorHandler class."""

import unittest
from unittest import mock
from api import deaggregator

from fastapi.testclient import TestClient
from tasks.ports import persistence


class DeaggregatorApiTest(unittest.TestCase):
  """Tests the /api/deaggregate endpoint and its underlying logic."""

  def setUp(self):
    """Set up mocks for external dependencies for each test."""
    super().setUp()

    self.client = TestClient(deaggregator.app)

    self.mock_workflow_repo = mock.MagicMock(
        spec=persistence.WorkflowExecutionPersistenceService
    )
    self.repo_patcher = mock.patch(
        "api.deaggregator.app_config.workflow_repo", self.mock_workflow_repo
    )
    self.repo_patcher.start()

    # Define common test data to be used across multiple tests.
    self.base_payload = {
        "topic": "social pulse test",
        "start_date": "2025-01-01",
        "end_date": "2025-08-31",
        "output": ["SENTIMENT_SCORE"],
        "include_justifications": False,
    }

  def tearDown(self):
    """Clean up patches after each test."""
    super().tearDown()
    self.repo_patcher.stop()

  @mock.patch("api.deaggregator.uuid.uuid4", return_value="mock-report-id-123")
  def test_video_and_comment_request_creates_both_workflows(
      self, mock_uuid
  ):  # pylint: disable=unused-argument
    """Tests that a valid request for both video and comments succeeds.

    Given a valid request for both video and comments,
    When the /api/deaggregate endpoint is called,
    Then it should return a 201 status,
    And create two linked workflows with a shared report_id,
    And return the correct response body.

    Args:
        mock_uuid: Injected by the @mock.patch decorator to control the
        return value of uuid.uuid4().
    """
    # Arrange
    payload = self.base_payload.copy()
    payload["sources"] = ["YOUTUBE_VIDEO", "YOUTUBE_COMMENT"]
    self.mock_workflow_repo.create_execution.side_effect = [
        "vid-exec-123",
        "com-exec-456",
    ]

    # Act
    response = self.client.post("/api/deaggregate", json=payload)

    # Assert Response
    self.assertEqual(response.status_code, 201)
    response_data = response.json()
    self.assertEqual(response_data["report_id"], "mock-report-id-123")
    self.assertEqual(response_data["topic"], "social pulse test")
    self.assertEqual(response_data["status"], "NEW")
    self.assertIn("created_on", response_data)

    # Assert Database Interaction
    self.assertEqual(self.mock_workflow_repo.create_execution.call_count, 2)
    calls = self.mock_workflow_repo.create_execution.call_args_list
    video_params = calls[0].args[0]
    comment_params = calls[1].args[0]

    self.assertEqual(video_params.report_id, "mock-report-id-123")
    self.assertEqual(comment_params.report_id, "mock-report-id-123")
    self.assertEqual(comment_params.parent_execution_id, "vid-exec-123")

  @mock.patch("api.deaggregator.uuid.uuid4", return_value="mock-report-id-456")
  def test_comment_only_request_implicitly_creates_parent(
      self, mock_uuid
  ):  # pylint: disable=unused-argument
    """Tests that a request for only comments creates a hidden parent.

    Given a valid request for only comments,
    When the /api/deaggregate endpoint is called,
    Then it should implicitly create a parent video workflow,
    And the response should only contain the comment workflow ID.

    Args:
      mock_uuid: Injected by the @mock.patch decorator.
    """
    # Arrange
    payload = self.base_payload.copy()
    payload["sources"] = ["YOUTUBE_COMMENT"]
    self.mock_workflow_repo.create_execution.side_effect = [
        "implicit-vid-789",
        "com-exec-101",
    ]

    # Act
    response = self.client.post("/api/deaggregate", json=payload)

    # Assert Response
    self.assertEqual(response.status_code, 201)

    # Assert Database Interaction
    self.assertEqual(self.mock_workflow_repo.create_execution.call_count, 2)
    calls = self.mock_workflow_repo.create_execution.call_args_list
    video_params = calls[0].args[0]
    comment_params = calls[1].args[0]

    self.assertEqual(video_params.report_id, "mock-report-id-456")
    self.assertEqual(comment_params.report_id, "mock-report-id-456")
    self.assertEqual(comment_params.parent_execution_id, "implicit-vid-789")

  def test_bad_request_missing_field_returns_422(self):
    """Tests that a missing field returns a 422 error.

    Given a request payload that is missing a required field,
    When the /api/deaggregate endpoint is called,
    Then FastAPI should automatically return a 422 Unprocessable Entity error.
    """
    # Arrange
    payload = self.base_payload.copy()
    del payload["topic"]  # Missing a required field

    # Act
    response = self.client.post("/api/deaggregate", json=payload)

    # Assert
    self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
  unittest.main()
