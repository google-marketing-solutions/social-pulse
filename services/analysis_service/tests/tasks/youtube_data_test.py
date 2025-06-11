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


import datetime
import unittest
from unittest import mock
import pandas as pd

from socialpulse_common import service
from socialpulse_common.messages import workflow_execution_pb2 as wfe
from tasks import core as tasks_core
from tasks import youtube_data
from tasks.ports import apis as ports_apis
from tasks.ports import persistence


class YoutubeDataTest(unittest.TestCase):

  def setUp(self):
    """Set up mocks for external dependencies."""
    super().setUp()

    # Mock Workflow Execution Parameter Loading
    self.mocked_wfe_params_loader_service = mock.Mock(
        spec=persistence.WorkflowExecutionPersistenceService
    )
    service.registry.register(
        persistence.WorkflowExecutionPersistenceService,
        self.mocked_wfe_params_loader_service,
    )

    # Mock YouTube API Client Service
    self.mock_api_client = mock.Mock(spec=ports_apis.YoutubeApiClient)
    service.registry.register(ports_apis.YoutubeApiClient, self.mock_api_client)

    # Mock Sentiment Data Repo Service
    self.mock_data_repo = mock.Mock(spec=persistence.SentimentDataRepo)
    self.mock_data_repo.exists.return_value = False
    service.registry.register(
        persistence.SentimentDataRepo, self.mock_data_repo
    )

    # Mock Config Settings
    self.settings_patcher = mock.patch("tasks.youtube_data.settings")
    self.mock_settings = self.settings_patcher.start()

    self.execution_id = "exec_id_123"
    self.required_task_mock = None

  def tearDown(self):
    """Clean up after each test."""
    super().tearDown()
    self.settings_patcher.stop()

  def _create_mock_workflow_exec(self):
    """Helper to create a standard mock workflow exec."""
    mock_exec = wfe.WorkflowExecutionParams()
    mock_exec.topic = "Test Topic"
    mock_exec.start_time.FromDatetime(datetime.datetime(2025, 4, 1))
    mock_exec.end_time.FromDatetime(datetime.datetime(2025, 5, 30))

    return mock_exec

  def test_output_returns_correct_target(self):
    """Verifies output() returns SentimentDataRepoTarget with correct name."""

    mock_exec = self._create_mock_workflow_exec()
    self.mocked_wfe_params_loader_service.load_execution.return_value = (
        mock_exec
    )
    task = youtube_data.FindYoutubeVideos(
        execution_id=self.execution_id, my_required_task=self.required_task_mock
    )
    expected_table_name = f"{task.task_family}_{self.execution_id}"

    output_target = task.output()

    # Assert
    self.assertIsInstance(output_target, tasks_core.SentimentDataRepoTarget)
    self.assertEqual(output_target.table_name, expected_table_name)
    self.assertEqual(output_target._sentiment_data_repo, self.mock_data_repo)

  def test_run_successful_workflow(self):
    """Tests the happy path: fetch, normalize, write."""
    mock_exec = self._create_mock_workflow_exec()
    self.mocked_wfe_params_loader_service.load_execution.return_value = (
        mock_exec
    )

    # Sample API Response
    raw_video_data = [
        {
            "id": {"videoId": "vid1"},
            "snippet": {
                "title": "Title 1",
                "description": "Desc 1",
                "channelId": "c1",
                "channelTitle": "Chan 1",
                "publishedAt": "2025-04-01T00:00:00Z",
            },
        },
        {
            "id": {"videoId": "vid2"},
            "snippet": {
                "title": "Title 2",
                "description": "Desc 2",
                "channelId": "c2",
                "channelTitle": "Chan 2",
                "publishedAt": "2025-05-30T00:00:00Z",
            },
        },
    ]
    self.mock_api_client.search_for_videos.return_value = raw_video_data

    # Define expected results
    expected_criteria = ports_apis.YoutubeSearchCriteria(
        query="Test Topic",
        language=ports_apis.Language.ENGLISH,
        sort_by=ports_apis.VideoResultsSortBy.RELEVANCE,
        max_results=1000,
        published_after=datetime.date(2025, 4, 1),
        published_before=datetime.date(2025, 5, 30),
    )
    expected_df = pd.DataFrame(
        {
            "videoId": ["vid1", "vid2"],
            "videoUrl": [
                "http://www.youtube.com/watch?v=vid1",
                "http://www.youtube.com/watch?v=vid2",
            ],
            "videoTitle": ["Title 1", "Title 2"],
            "videoDescription": ["Desc 1", "Desc 2"],
            "channelId": ["c1", "c2"],
            "channelTitle": ["Chan 1", "Chan 2"],
            "publishedAt": ["2025-04-01T00:00:00Z", "2025-05-30T00:00:00Z"],
        }
    )

    task = youtube_data.FindYoutubeVideos(
        execution_id=self.execution_id, my_required_task=self.required_task_mock
    )
    expected_table_name = task.output().table_name

    # Execute the task
    task.run()

    # Verify mocks were called as expected
    self.mock_api_client.search_for_videos.assert_called_once_with(
        expected_criteria
    )
    self.mock_data_repo.write_sentiment_data.assert_called_once()

    # Compare DataFrame passed to write_sentiment_data
    call_args, _ = self.mock_data_repo.write_sentiment_data.call_args
    self.assertEqual(call_args[0], expected_table_name)
    pd.testing.assert_frame_equal(call_args[1], expected_df)

  def test_run_raises_error_when_no_videos_found(self):
    """Tests that run raises ValueError if API returns no videos."""

    mock_exec = self._create_mock_workflow_exec()
    self.mocked_wfe_params_loader_service.load_execution.return_value = (
        mock_exec
    )
    self.mock_api_client.search_for_videos.return_value = []

    # Assert
    with self.assertRaises(ValueError) as err_context:
      task = youtube_data.FindYoutubeVideos(
          execution_id=self.execution_id,
          my_required_task=self.required_task_mock
      )
      task.run()

    self.assertIn("No videos found", str(err_context.exception))


if __name__ == "__main__":
  unittest.main()
