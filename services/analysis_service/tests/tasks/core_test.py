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
from socialpulse_common import service
from tasks import core
from tasks.ports import persistence


class RequiredTask(luigi.WrapperTask):
  def requires(self):
    return None


class TestChildSentimentTask(core.SentimentTask):
  task_namespace = "test_namespace"

  def output(self):
    return None

  def run(self):
    pass


class CoreTest(unittest.TestCase):
  def setUp(self):
    super().setUp()

    self.mocked_wfe_params_loader_service = mock.Mock()
    self.mock_execution_params = mock.Mock()

    self.mocked_wfe_params_loader_service.load_execution.return_value = (
        self.mock_execution_params
    )

    service.registry.register(
        persistence.WorkflowExecutionLoaderService,
        self.mocked_wfe_params_loader_service
    )

  def test_sentiment_task_loads_workflow_execution_params_using_id(self):
    """Loads workflow execution parameters using the provided ID.

    Given an implementation of SentimentTask
    When it's instantiated with an execution ID of "some_execution_id'
    Then the execution params should be loaded from the service
    """
    task = TestChildSentimentTask("some_execution_id", RequiredTask())

    self.assertEqual(self.mock_execution_params, task.workflow_exec)

  def test_task_data_set_name_constructed_from_family_and_execution_id(self):
    """Constructs a data set name from the task family and execution ID.

    Given an implementation of SentimentTask
    And it's instantiated with a task family of "test_namespace"
    When it's instantiated with an execution ID of "some_execution_id"
    Then the data set name should be constructed as
        "test_namespace.TestChildSentimentTask_some_execution_id"
    """
    task = TestChildSentimentTask("some_execution_id", RequiredTask())

    self.assertEqual(
        "test_namespace.TestChildSentimentTask_some_execution_id",
        task.dataset_name
    )
