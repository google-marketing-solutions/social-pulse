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
"""Unit tests for the runner_entry FastAPI application."""

import datetime
import unittest
from unittest import mock

from api import runner_entry
from fastapi.testclient import TestClient
from socialpulse_common import service
from socialpulse_common.messages import common as common_msg
from socialpulse_common.messages import sentiment_report as report_msg
from socialpulse_common.persistence import postgresdb_client as client
from tasks.ports import persistence


class RunnerEntryTest(unittest.TestCase):
  """Tests the runner_entry FastAPI endpoint."""

  def setUp(self):
    """Sets up the test environment."""
    super().setUp()
    self.client = TestClient(runner_entry.app)
    self._mock_config_settings()
    self._mock_postgres_client()
    self._mock_workflow_execution_repo()

  def _mock_config_settings(self):
    """Mocks configuration settings."""
    self._mock_settings = mock.Mock()
    self._mock_settings.db.host = "test_db_host"
    self._mock_settings.db.port = 1234
    self._mock_settings.db.name = "test_db_name"
    self._mock_settings.db.username = "test_db_user"
    self._mock_settings.db.password = "test_db_password"

    patcher = mock.patch("socialpulse_common.config.Settings")
    self._mock_settings_cls = patcher.start()
    self.addCleanup(patcher.stop)
    self._mock_settings_cls.return_value = self._mock_settings

  def _mock_postgres_client(self):
    """Mocks the PostgresDbClient."""
    patcher = mock.patch.object(client, "PostgresDbClient")
    self.mock_postgres_client_cls = patcher.start()
    self.addCleanup(patcher.stop)

  def _mock_workflow_execution_repo(self):
    self.mock_repo = mock.Mock(
        spec=persistence.WorkflowExecutionPersistenceService
    )
    patcher = mock.patch.object(
        service.registry,
        "get",
        return_value=self.mock_repo,
    )
    self.mock_registry_get = patcher.start()
    self.addCleanup(patcher.stop)

  def test_deaggregate_report_with_youtube_video(self):
    """Tests de-aggregation for a report with only YouTube video source.

    Given a sentiment report with YOUTUBE_VIDEO as the source.
    When the /api/run_report endpoint is called.
    Then a single workflow execution for video is created.
    """
    # Arrange
    self.mock_repo.create_execution.return_value = "video-exec-id"
    report = report_msg.SentimentReport(
        report_id="test-report",
        topic="Test Topic",
        sources=[common_msg.SocialMediaSource.YOUTUBE_VIDEO],
        start_time=datetime.datetime.now(datetime.timezone.utc),
        end_time=datetime.datetime.now(datetime.timezone.utc),
        data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
        include_justifications=True,
    )

    # Act
    response = self.client.post(
        "/api/run_report", json=report.model_dump(mode="json")
    )

    # Assert
    self.assertEqual(response.status_code, 201)
    self.mock_repo.create_execution.assert_called_once()
    call_args = self.mock_repo.create_execution.call_args[0][0]
    self.assertEqual(
        call_args.source, common_msg.SocialMediaSource.YOUTUBE_VIDEO
    )

  def test_deaggregate_report_with_youtube_comment(self):
    """Tests de-aggregation for a report with only YouTube comment source.

    Given a sentiment report with YOUTUBE_COMMENT as the source.
    When the /api/run_report endpoint is called.
    Then two workflow executions are created: one for video and one for
    comments.
    """
    # Arrange
    self.mock_repo.create_execution.side_effect = [
        "video-exec-id",
        "comment-exec-id",
    ]
    report = report_msg.SentimentReport(
        report_id="test-report",
        topic="Test Topic",
        sources=[common_msg.SocialMediaSource.YOUTUBE_COMMENT],
        start_time=datetime.datetime.now(datetime.timezone.utc),
        end_time=datetime.datetime.now(datetime.timezone.utc),
        data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
        include_justifications=True,
    )

    # Act
    response = self.client.post(
        "/api/run_report", json=report.model_dump(mode="json")
    )

    # Assert
    self.assertEqual(response.status_code, 201)
    self.assertEqual(self.mock_repo.create_execution.call_count, 2)
    video_call_args = self.mock_repo.create_execution.call_args_list[0][0][0]
    comment_call_args = self.mock_repo.create_execution.call_args_list[1][0][0]
    self.assertEqual(
        video_call_args.source, common_msg.SocialMediaSource.YOUTUBE_VIDEO
    )
    self.assertEqual(
        comment_call_args.source, common_msg.SocialMediaSource.YOUTUBE_COMMENT
    )
    self.assertEqual(comment_call_args.parent_execution_id, "video-exec-id")

  def test_deaggregate_report_with_video_and_comment(self):
    """Tests de-aggregation with both video and comment sources.

    Given a sentiment report with both YOUTUBE_VIDEO and YOUTUBE_COMMENT.
    When the /api/run_report endpoint is called.
    Then two workflow executions are created with the correct dependency.
    """
    # Arrange
    self.mock_repo.create_execution.side_effect = [
        "video-exec-id",
        "comment-exec-id",
    ]
    report = report_msg.SentimentReport(
        report_id="test-report",
        topic="Test Topic",
        sources=[
            common_msg.SocialMediaSource.YOUTUBE_VIDEO,
            common_msg.SocialMediaSource.YOUTUBE_COMMENT,
        ],
        start_time=datetime.datetime.now(datetime.timezone.utc),
        end_time=datetime.datetime.now(datetime.timezone.utc),
        data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
        include_justifications=True,
    )

    # Act
    response = self.client.post(
        "/api/run_report", json=report.model_dump(mode="json")
    )

    # Assert
    self.assertEqual(response.status_code, 201)
    self.assertEqual(self.mock_repo.create_execution.call_count, 2)
    video_call_args = self.mock_repo.create_execution.call_args_list[0][0][0]
    comment_call_args = self.mock_repo.create_execution.call_args_list[1][0][0]
    self.assertEqual(
        video_call_args.source, common_msg.SocialMediaSource.YOUTUBE_VIDEO
    )
    self.assertEqual(
        comment_call_args.source, common_msg.SocialMediaSource.YOUTUBE_COMMENT
    )
    self.assertEqual(comment_call_args.parent_execution_id, "video-exec-id")

  def test_deaggregate_report_with_no_youtube_sources(self):
    """Tests that no workflows are created if there are no YouTube sources.

    Given a sentiment report with no YouTube-related sources.
    When the /api/run_report endpoint is called.
    Then no workflow executions are created.
    """
    # Arrange
    report = report_msg.SentimentReport(
        report_id="test-report",
        topic="Test Topic",
        sources=[],  # No relevant sources
        start_time=datetime.datetime.now(datetime.timezone.utc),
        end_time=datetime.datetime.now(datetime.timezone.utc),
        data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
        include_justifications=True,
    )

    # Act
    response = self.client.post(
        "/api/run_report", json=report.model_dump(mode="json")
    )

    # Assert
    self.assertEqual(response.status_code, 201)
    self.mock_repo.create_execution.assert_not_called()

  def test_deaggregate_report_handles_validation_error(self):
    """Tests that a 422 error is returned for a validation error.

    Given an invalid report payload.
    When the /api/run_report endpoint is called.
    Then the endpoint returns a 422 Unprocessable Entity status.
    """
    # Act
    response = self.client.post("/api/run_report", json={"sources": "invalid"})

    # Assert
    self.assertEqual(response.status_code, 422)

  def test_deaggregate_report_handles_db_connection_error(self):
    """Tests that a 500 error is returned for a db connection error.

    Given a database connection error.
    When the /api/run_report endpoint is called.
    Then the endpoint returns a 500 Internal Server Error status.
    """
    # Arrange
    self.mock_postgres_client_cls.side_effect = Exception(
        "DB connection error"
    )
    runner_entry.is_initialized = False
    report = report_msg.SentimentReport(
        report_id="test-report",
        topic="Test Topic",
        sources=[],
        start_time=datetime.datetime.now(datetime.timezone.utc),
        end_time=datetime.datetime.now(datetime.timezone.utc),
        data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
        include_justifications=True,
    )

    # Act
    response = self.client.post(
        "/api/run_report", json=report.model_dump(mode="json")
    )

    # Assert
    self.assertEqual(response.status_code, 500)


if __name__ == "__main__":
  unittest.main()
