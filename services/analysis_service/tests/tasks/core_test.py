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

from socialpulse_common import service
import tasks
import tasks.core


class EmptyChildSentimentTask(tasks.core.SentimentTask):
  def requires(self):
    return None

  def output(self):
    return None

  def run(self):
    pass


class CoreTest(unittest.TestCase):
  def setUp(self):
    super().setUp()

    self.mocked_wfe_params_loader_service = mock.Mock()
    service.registry.register(
        tasks.core.WorkflowExecutionLoaderService,
        self.mocked_wfe_params_loader_service
    )

  def test_sentiment_task_loads_workflow_execution_params_using_id(self):
    """Loads workflow execution parameters using the provided ID.

    Given an implementation of SentimentTask
    When it's instantiated with an execution ID of "some_execution_id'
    Then the execution params should be loaded from the service
    """
    mock_execution_params = mock.Mock()
    self.mocked_wfe_params_loader_service.load_execution.return_value = (
        mock_execution_params
    )

    task = EmptyChildSentimentTask("some_execution_id")

    self.assertEqual(mock_execution_params, task.workflow_exec)
