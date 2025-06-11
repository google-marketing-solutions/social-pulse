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

import unittest
from unittest import mock

import luigi
import pandas as pd
from socialpulse_common import service
from socialpulse_common.messages import workflow_execution_pb2 as wfe
from tasks import core as tasks_core
from tasks import youtube_comments
from tasks.ports import apis as ports_apis
from tasks.ports import persistence


TEST_RAW_COMMENTS_JSON_DATA = [
    {
        "id": "top1",
        "snippet": {
            "videoId": "vidWithReplies",
            "topLevelComment": {
                "snippet": {
                    "authorChannelId": {"value": "authorA"},
                    "publishedAt": "dateA",
                    "textOriginal": "Text A",
                    "likeCount": 10,
                }
            },
            "totalReplyCount": 1,
        },
        "replies": {
            "comments": [
                {
                    "id": "top1.reply1",
                    "snippet": {
                        "authorChannelId": {"value": "authorB"},
                        "publishedAt": "dateB",
                        "textOriginal": "Reply B",
                        "likeCount": 2,
                        "parentId": "top1",
                    },
                }
            ]
        },
    }
]


class YoutubeCommentsTest(unittest.TestCase):
  """Unit tests for the FindYoutubeComments Luigi task."""

  def _setup_mock_workflow_exec_loader(self):
    """Sets up and registers the mock WorkflowExecutionLoaderService."""
    self.mocked_wfe_params_loader_service = mock.Mock(
        spec=persistence.WorkflowExecutionPersistenceService
    )

    self.mock_workflow_exec = mock.Mock(spec=wfe.WorkflowExecutionParams)

    self.mock_workflow_exec.topic = "CommentTaskTest"
    self.mocked_wfe_params_loader_service.load_execution.return_value = (
        self.mock_workflow_exec
    )

    service.registry.register(
        persistence.WorkflowExecutionPersistenceService,
        self.mocked_wfe_params_loader_service,
    )

  def _setup_mock_youtube_api_client(self):
    """Sets up and registers the mock YoutubeApiClient."""
    self.mock_api_client = mock.Mock(spec=ports_apis.YoutubeApiClient)
    self.mock_api_client.get_comments_for_videos.return_value = (
        TEST_RAW_COMMENTS_JSON_DATA
    )
    service.registry.register(ports_apis.YoutubeApiClient, self.mock_api_client)

  def _setup_mock_data_repo(self):
    """Sets up and registers the mock SentimentDataRepo."""
    self.mock_data_repo = mock.Mock(spec=persistence.SentimentDataRepo)
    self.mock_data_repo.exists.return_value = False
    service.registry.register(
        persistence.SentimentDataRepo, self.mock_data_repo
    )

  def _setup_mock_settings(self):
    """Sets up the patch for config settings."""
    self.settings_patcher = mock.patch("tasks.youtube_comments.settings")
    self.mock_settings = self.settings_patcher.start()

  def _setup_mock_required_task(self):
    """Sets up the mock for the required FindYoutubeVideos task's output."""
    self.mock_input_video_target = mock.Mock(
        spec=tasks_core.SentimentDataRepoTarget
    )
    self.mock_input_video_target.table_name = (
        "FindYoutubeVideos_mock_input_for_comments"
    )
    self.mock_input_video_target.exists.return_value = True

    self.mock_required_video_task = mock.Mock(spec=luigi.Task)
    self.mock_required_video_task.requires.return_value = []
    self.mock_required_video_task.output.return_value = (
        self.mock_input_video_target
    )

  def setUp(self):
    """Set up a controlled environment with mocks before each test."""
    super().setUp()

    self._setup_mock_workflow_exec_loader()
    self._setup_mock_youtube_api_client()
    self._setup_mock_data_repo()
    self._setup_mock_settings()
    self._setup_mock_required_task()

    self.execution_id = "exec_id_123"

  def tearDown(self):
    """Clean up after each test."""
    super().tearDown()
    self.settings_patcher.stop()

  def test_run_loads_input_from_required_task_target(self):
    """Verifies that run() loads data from preceding task's output target."""
    expected_input_df = pd.DataFrame({"videoId": ["vidTest"]})
    self.mock_input_video_target.load_sentiment_data.return_value = (
        expected_input_df
    )
    task = youtube_comments.FindYoutubeComments(
        execution_id=self.execution_id,
        my_required_task=self.mock_required_video_task,
    )

    task.run()
    self.mock_input_video_target.load_sentiment_data.assert_called_once_with()

  def test_run_successful_workflow_with_replies(self):
    """Tests main run logic: load input, fetch comments, flatten, write."""

    # Configure input data (from FindYoutubeVideos)
    input_videos_df = pd.DataFrame({"videoId": ["vidWithReplies"]})
    self.mock_input_video_target.load_sentiment_data.return_value = (
        input_videos_df
    )

    # Define expected DataFrame after flattening
    expected_comments_df = pd.DataFrame(
        {
            "commentId": ["top1", "top1.reply1"],
            "videoId": ["vidWithReplies", "vidWithReplies"],
            "authorId": ["authorA", "authorB"],
            "publishedAt": ["dateA", "dateB"],
            "text": ["Text A", "Reply B"],
            "likeCount": [10, 2],
            "numOfReplies": [1, 0],  # Top-level has 1, reply has 0
            "parentId": [pd.NA, "top1"],
        }
    ).astype({"likeCount": "int64", "numOfReplies": "int64"})

    task = youtube_comments.FindYoutubeComments(
        execution_id=self.execution_id,
        my_required_task=self.mock_required_video_task,
    )
    expected_output_table_name = task.output().table_name
    task.run()

    # Assert
    self.mock_api_client.get_comments_for_videos.assert_called_once_with(
        ["vidWithReplies"]
    )
    self.mock_data_repo.write_sentiment_data.assert_called_once()
    call_args, _ = self.mock_data_repo.write_sentiment_data.call_args
    self.assertEqual(call_args[0], expected_output_table_name)
    pd.testing.assert_frame_equal(
        call_args[1], expected_comments_df, check_dtype=False
    )


if __name__ == "__main__":
  unittest.main()
