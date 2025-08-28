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

import datetime
import unittest
from unittest import mock

from api import deaggregator
from socialpulse_common import service
from socialpulse_common.messages import workflow_execution as wfe
from tasks.ports import persistence


class DeaggregatorHandlerTest(unittest.TestCase):
  """Tests the core logic of the DeaggregatorHandler."""

  def setUp(self):
    """Set up mocks for external dependencies for each test."""
    super().setUp()

    # Mock the persistence service, which is the sole dependency of the handler.
    # This mock will be injected via the service registry.
    self.mock_workflow_repo = mock.Mock(
        spec=persistence.WorkflowExecutionPersistenceService
    )
    service.registry.register(
        persistence.WorkflowExecutionPersistenceService, self.mock_workflow_repo
    )

    # Define common test data to be used across multiple tests.
    self.topic = "social pulse test"
    self.start_date = datetime.date(2025, 1, 1)
    self.end_date = datetime.date(2024, 8, 31)
    self.outputs = [wfe.SentimentDataType.SENTIMENT_SCORE]

  def test_request_with_video_and_comment_creates_both_with_parent_link(self):
    """Tests the happy path where both video and comments are requested.

    Given a request contains both YOUTUBE_VIDEO and YOUTUBE_COMMENT sources,
    When the handler processes the request,
    Then a video workflow is created with no parent,
    And a comment workflow is created with the video workflow's ID as its parent
    And the response contains IDs for both workflows.
    """
    # Arrange: Mock the DB to return a unique ID for each creation call.
    self.mock_workflow_repo.create_execution.side_effect = [
        "vid-exec-123",  # First call returns the video ID
        "com-exec-456",  # Second call returns the comment ID
    ]
    sources = [
        wfe.SocialMediaSource.YOUTUBE_VIDEO,
        wfe.SocialMediaSource.YOUTUBE_COMMENT,
    ]

    # Act: Instantiate the handler and process the request.
    handler = deaggregator.DeaggregatorHandler(
        topic=self.topic,
        start_date=self.start_date,
        end_date=self.end_date,
        sources=sources,
        outputs=self.outputs,
    )
    handler.process_request()

    # Assert: Verify the correct workflows were created and linked.
    self.assertEqual(self.mock_workflow_repo.create_execution.call_count, 2)
    calls = self.mock_workflow_repo.create_execution.call_args_list

    # First call should be the parent video workflow.
    video_params_call = calls[0].args[0]
    self.assertEqual(
        video_params_call.source, wfe.SocialMediaSource.YOUTUBE_VIDEO
    )
    self.assertIsNone(video_params_call.parent_execution_id)

    # Second call should be the child comment workflow, linked to the first.
    comment_params_call = calls[1].args[0]
    self.assertEqual(
        comment_params_call.source, wfe.SocialMediaSource.YOUTUBE_COMMENT
    )
    self.assertEqual(comment_params_call.parent_execution_id, "vid-exec-123")

  def test_request_with_video_and_comment_returns_correct_response(self):
    """Tests that the returned dictionary is correctly formatted.

    Given a request contains both YOUTUBE_VIDEO and YOUTUBE_COMMENT sources,
    When the handler processes the request,
    Then the response dictionary contains the correct execution IDs for both
    sources.
    """
    # Mock the DB to return a unique ID for each creation call.
    self.mock_workflow_repo.create_execution.side_effect = [
        "vid-exec-123",
        "com-exec-456",
    ]
    sources = [
        wfe.SocialMediaSource.YOUTUBE_VIDEO,
        wfe.SocialMediaSource.YOUTUBE_COMMENT,
    ]

    # Instantiate the handler and process the request.
    handler = deaggregator.DeaggregatorHandler(
        topic=self.topic,
        start_date=self.start_date,
        end_date=self.end_date,
        sources=sources,
        outputs=self.outputs,
    )
    result = handler.process_request()

    # Assert: Verify the returned dictionary is correct
    expected_dict = {
        "YOUTUBE_VIDEO": "vid-exec-123",
        "YOUTUBE_COMMENT": "com-exec-456",
    }
    self.assertDictEqual(result, expected_dict)

  def test_request_with_comment_only_implicitly_creates_video_parent(self):
    """Tests that a request for comments alone creates a hidden parent video workflow.

    Given a request contains only the YOUTUBE_COMMENT source,
    When the handler processes the request,
    Then a video workflow is still created first to act as the parent,
    And a comment workflow is created with the new video ID as its parent.
    And the response contains ONLY the ID for the requested comment workflow.
    """
    # Arrange
    self.mock_workflow_repo.create_execution.side_effect = [
        "implicit-vid-789",
        "com-exec-101",
    ]
    sources = [wfe.SocialMediaSource.YOUTUBE_COMMENT]

    # Act
    handler = deaggregator.DeaggregatorHandler(
        topic=self.topic,
        start_date=self.start_date,
        end_date=self.end_date,
        sources=sources,
        outputs=self.outputs,
    )
    result = handler.process_request()

    # Assert: The database interaction should be identical to the previous test.
    self.assertEqual(self.mock_workflow_repo.create_execution.call_count, 2)
    calls = self.mock_workflow_repo.create_execution.call_args_list
    self.assertEqual(
        calls[0].args[0].source, wfe.SocialMediaSource.YOUTUBE_VIDEO
    )
    self.assertEqual(calls[1].args[0].parent_execution_id, "implicit-vid-789")

    # Assert the final response is correct
    self.assertNotIn("YOUTUBE_VIDEO", result)
    self.assertIn("YOUTUBE_COMMENT", result)
    self.assertEqual(result["YOUTUBE_COMMENT"], "com-exec-101")
    self.assertEqual(len(result), 1)

  def test_request_with_video_only_creates_single_workflow(self):
    """Tests that a request for only videos works correctly.

    Given a request contains only the YOUTUBE_VIDEO source,
    When the handler processes the request,
    Then only one workflow is created (the video workflow),
    And the response contains only the video workflow ID.
    """
    # Arrange
    self.mock_workflow_repo.create_execution.return_value = "vid-exec-only-321"
    sources = [wfe.SocialMediaSource.YOUTUBE_VIDEO]

    # Act
    handler = deaggregator.DeaggregatorHandler(
        topic=self.topic,
        start_date=self.start_date,
        end_date=self.end_date,
        sources=sources,
        outputs=self.outputs,
    )
    result = handler.process_request()

    # Assert
    self.mock_workflow_repo.create_execution.assert_called_once()
    video_params_call = self.mock_workflow_repo.create_execution.call_args.args[
        0
    ]
    self.assertEqual(
        video_params_call.source, wfe.SocialMediaSource.YOUTUBE_VIDEO
    )
    self.assertIsNone(video_params_call.parent_execution_id)

    self.assertIn("YOUTUBE_VIDEO", result)
    self.assertEqual(result["YOUTUBE_VIDEO"], "vid-exec-only-321")
    self.assertEqual(len(result), 1)


if __name__ == "__main__":
  unittest.main()
