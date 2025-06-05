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

import luigi
import sentiment_task_mixins as test_mixins
from tasks import core


class RequiredTask(luigi.WrapperTask):
  def requires(self):
    return None


class TestChildSentimentTask(core.SentimentTask):
  task_namespace = "test_namespace"

  def run(self):
    pass


class CoreTest(
    unittest.TestCase,
    test_mixins.SetupMockSentimentTaskDepependenciesMixin
):
  def setUp(self):
    super().setUp()

    # Need to clear Luigi's task cache, otherwise it'll re-use whatever test
    # child task created by the first executed test.
    luigi.Task.clear_instance_cache()

    self.setup_mock_setniment_data_repo()
    self.setup_mock_workflow_params()

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

  def test_output_returns_sentiment_data_repo_target_with_correct_table_name(
      self
  ):
    """Returns a SentimentDataRepoTarget with the correct table name.

    Given an implementation of SentimentTask
    When its output() method is called
    Then it should return a SentimentDataRepoTarget instance
    And that instance should have its table_name attribute set to the task's
        dataset_name.
    """
    task = TestChildSentimentTask("some_execution_id", RequiredTask())
    expected_table_name = task.dataset_name

    output_target = task.output()

    self.assertIsInstance(output_target, core.SentimentDataRepoTarget)
    self.assertEqual(output_target.table_name, expected_table_name)


class WorkflowExecutionParamsLoaderMixinTest(
    unittest.TestCase,
    test_mixins.SetupMockSentimentTaskDepependenciesMixin
):
  def setUp(self):
    super().setUp()

    # Need to clear Luigi's task cache, otherwise it'll re-use whatever test
    # child task created by the first executed test.
    luigi.Task.clear_instance_cache()

    self.setup_mock_setniment_data_repo()
    self.setup_mock_workflow_params()

  def test_sentiment_task_loads_workflow_execution_params_using_id(self):
    """Loads workflow execution parameters using the provided ID.

    Given an implementation of SentimentTask
    When it's instantiated with an execution ID of "some_execution_id'
    Then the execution params should be loaded from the service
    """
    task = TestChildSentimentTask("some_execution_id", RequiredTask())

    self.mock_wfe_params_loader_service.load_execution.assert_called_once_with(
        "some_execution_id"
    )
    self.assertEqual(self.mock_execution_params, task.workflow_exec)


if __name__ == "__main__":
  unittest.main()
