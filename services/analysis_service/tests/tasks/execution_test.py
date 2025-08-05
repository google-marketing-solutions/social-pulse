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

import sentiment_task_mixins as test_mixins
from socialpulse_common.messages import common as common_msg
from socialpulse_common.messages import workflow_execution as wfe
from tasks import core as tasks_core
from tasks import execution


class ExecutionTest(
    unittest.TestCase,
    test_mixins.SetupMockSentimentTaskDepependenciesMixin
):
  def setUp(self):
    super().setUp()
    self.setup_all_mock_dependencies()

    self.mock_execution_params.status = wfe.Status.NEW
    self.mock_execution_params.last_completed_task_id = None
    self.mock_execution_params.data_output = [
        common_msg.SentimentDataType.SENTIMENT_SCORE
    ]

  def assert_task_in_list(
      self,
      task_list: list[tasks_core.SentimentTask],
      task_cls: type[tasks_core.SentimentTask]
  ) -> None:
    """Asserts that a task of the given class is present in the task list.

    Args:
      task_list: A list of luigi.Task instances.
      task_cls: The class of the task to check for.

    Raises:
      AssertionError: If no task of the given class is found in the list.
    """
    self.assertTrue(
        any(isinstance(task, task_cls) for task in task_list),
        f"Task of type {task_cls} should be in the list, but it was not found."
    )

  def assert_task_not_in_list(
      self,
      task_list: list[tasks_core.SentimentTask],
      task_cls: type[tasks_core.SentimentTask]
  ) -> None:
    """Asserts that a task of the given class is NOT present in the task list.

    Args:
      task_list: A list of luigi.Task instances.
      task_cls: The class of the task to check for.

    Raises:
      AssertionError: If a task of the given class is found in the list.
    """
    self.assertFalse(
        any(isinstance(task, task_cls) for task in task_list),
        f"Task of type {task_cls} should not be in the list, but it was found."
    )

  def test_returns_empty_list_if_workflow_exec_param_status_is_completed(self):
    """Returns an empty list if the workflow execution parameter status is completed.

    Given the workflow execution parameter status is COMPLETED
    When the WorkflowExecution task starts its lifecycle.
    Then an empty list is returned.
    """
    self.mock_execution_params.status = wfe.Status.COMPLETED

    execution_task = execution.WorkflowExecution(execution_id="test_id")
    tasks = execution_task.requires()
    self.assertEqual(list(tasks), [])

  def test_fails_if_workflow_exec_param_source_is_unknown(self):
    """Fails if the workflow execution parameter source is unknown.

    Given the workflow execution parameter source is UNKNOWN
    When the WorkflowExecution task starts its lifecycle.
    Then a ValueError is raised
    """
    self.mock_execution_params.source = (
        common_msg.SocialMediaSource.UNKNOWN
    )

    with self.assertRaises(ValueError) as ve:
      execution_task = execution.WorkflowExecution(execution_id="test_id")
      execution_task.complete()

    self.assertIn("Unknown social media source", str(ve.exception))
    self.mock_wfe_params_loader_service.update_status.assert_called_once_with(
        "test_id",
        wfe.Status.FAILED
    )

  def test_adds_retrieve_youtube_video_for_video_content(self):
    """Adds the FindYoutubeVideos task to the task chain for video content.

    Given the workflow execution parameter source is Youtube video
    When the WorkflowExecution task starts its lifecycle.
    Then FindYoutubeVideos task is added to the task chain
    And FindYoutubeComments task is not added.
    """
    self.mock_execution_params.source = (
        common_msg.SocialMediaSource.YOUTUBE_VIDEO
    )

    execution_task = execution.WorkflowExecution(execution_id="test_id")
    # requires() produces a list of lists of tasks.
    task_list = list(execution_task.requires())[0]

    self.assert_task_in_list(
        task_list,
        execution.youtube_data.FindYoutubeVideos
    )
    self.assert_task_not_in_list(
        task_list,
        execution.youtube_comments.FindYoutubeComments
    )

  def test_adds_retrieve_youtube_comments_for_video_comments(self):
    """Adds the find videos and comments tasks to the task chain for comments.

    Given the workflow execution parameter source is Youtube comments
    When the WorkflowExecution task starts its lifecycle
    And FindYoutubeComments task is added to the task chain
    """
    self.mock_execution_params.source = (
        common_msg.SocialMediaSource.YOUTUBE_COMMENT
    )

    execution_task = execution.WorkflowExecution(execution_id="test_id")
    # requires() produces a list of lists of tasks.
    task_list = list(execution_task.requires())[0]

    self.assert_task_in_list(
        task_list,
        execution.youtube_comments.FindYoutubeComments
    )

  def test_restarts_workflow_if_last_completed_task_is_unknown(self):
    """Restarts a workflow if the last completed task is unknown.

    Given a workflow where the last completed task is unknown
    When the WorkflowExecution task starts its lifecycle
    Then the FindYoutubeVideos won't be in the task chain
    """
    self.mock_execution_params.status = wfe.Status.IN_PROGRESS
    self.mock_execution_params.last_completed_task_id = "foo"
    self.mock_execution_params.source = (
        common_msg.SocialMediaSource.YOUTUBE_VIDEO
    )

    execution_task = execution.WorkflowExecution(execution_id="test_id")
    # requires() produces a list of lists of tasks.
    task_list = list(execution_task.requires())[0]

    self.assert_task_in_list(
        task_list,
        execution.youtube_data.FindYoutubeVideos
    )
