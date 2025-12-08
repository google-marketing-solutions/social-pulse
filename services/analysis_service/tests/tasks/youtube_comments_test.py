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
from socialpulse_common.messages import workflow_execution as wfe
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

  def setUp(self):
    """Set up a controlled environment with mocks before each test."""
    super().setUp()

    self._setup_mock_workflow_exec_loader()
    self._setup_mock_youtube_api_client()
    self._setup_mock_data_repo()
    self._setup_mock_required_task()

    self.execution_id = "exec_id_123"

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

  def test_run_loads_input_from_required_task_target(self):
    """Tests that run() loads data from the preceding task's output.

    Given a FindYoutubeComments task with a mocked input target.
    When the run method is invoked.
    Then the input target's load_sentiment_data method is called once.
    """
    expected_input_df = pd.DataFrame(
        {
            "videoId": ["vidTest"],
            "summary": ["a video summary"]
        }
    )
    self.mock_input_video_target.load_sentiment_data.return_value = (
        expected_input_df
    )
    task = youtube_comments.FindYoutubeComments(
        execution_id=self.execution_id,
        my_required_task=self.mock_required_video_task,
    )

    task.run()
    self.mock_input_video_target.load_sentiment_data.assert_called_once_with()

  def test_run_writes_successfully(self):
    """Tests that run() successfully writes flattened comment data.

    Given a FindYoutubeComments task with mocked video data and an API
      client returning comments with replies.
    When the run method is invoked.
    Then the API client is called, and the flattened comment data is written
      to the sentiment data repository.
    """
    # Configure input data (from FindYoutubeVideos)
    input_videos_df = pd.DataFrame(
        {
            "videoId": ["vidWithReplies"],
            "summary": ["a video summary"]
        }
    )
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
            "summary": ["a video summary", "a video summary"],
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

  def test_run_handles_videos_with_no_comments(self):
    """Tests that run() handles videos that have no comments.

    Given a FindYoutubeComments task where the API returns an empty list of
      comments for a video.
    When the run method is invoked.
    Then an empty DataFrame is written to the output.
    """
    input_videos_df = pd.DataFrame(
        {
            "videoId": ["vidWithNoComments"],
            "summary": ["a video summary"]
        }
    )
    self.mock_input_video_target.load_sentiment_data.return_value = (
        input_videos_df
    )
    self.mock_api_client.get_comments_for_videos.return_value = []

    task = youtube_comments.FindYoutubeComments(
        execution_id=self.execution_id,
        my_required_task=self.mock_required_video_task,
    )

    task.run()

    self.mock_data_repo.write_sentiment_data.assert_called_once()
    call_args, _ = self.mock_data_repo.write_sentiment_data.call_args
    written_df = call_args[1]
    self.assertTrue(written_df.empty)

  def test_run_raises_exception_on_data_load_error(self):
    """Tests that an exception during data loading is propagated.

    Given a FindYoutubeComments task where loading input data fails.
    When the run method is invoked.
    Then an exception is raised.
    """
    self.mock_input_video_target.load_sentiment_data.side_effect = Exception(
        "Test Exception"
    )
    task = youtube_comments.FindYoutubeComments(
        execution_id=self.execution_id,
        my_required_task=self.mock_required_video_task,
    )
    with self.assertRaises(Exception):
      task.run()

  def test_run_raises_exception_malformed_api_response(self):
    """Tests that run() raises an exception for malformed API data.

    Given a FindYoutubeComments task where the API returns comments with
      missing fields.
    When the run method is invoked.
    Then a KeyError is raised during data processing.
    """
    # This malformed data is missing 'textOriginal' in the top level
    malformed_comments = [
        {
            "id": "top1",
            "snippet": {
                "videoId": "vidWithReplies",
                "topLevelComment": {
                    "snippet": {
                        "authorChannelId": {"value": "authorA"},
                        "publishedAt": "dateA",
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
                            "likeCount": 2,
                            "textOriginal": "Text A",
                            "parentId": "top1",
                        },
                    }
                ]
            },
        }
    ]
    self.mock_api_client.get_comments_for_videos.return_value = (
        malformed_comments
    )
    input_videos_df = pd.DataFrame(
        {
            "videoId": ["vidWithReplies"],
            "summary": ["a video summary"]
        }
    )
    self.mock_input_video_target.load_sentiment_data.return_value = (
        input_videos_df
    )

    task = youtube_comments.FindYoutubeComments(
        execution_id=self.execution_id,
        my_required_task=self.mock_required_video_task,
    )

    with self.assertRaises(KeyError):
      task.run()
