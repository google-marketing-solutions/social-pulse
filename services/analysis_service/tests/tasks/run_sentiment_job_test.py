# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from unittest import mock

from socialpulse_common import service
from tasks import core as tasks_core
from tasks import run_sentiment_job
from tasks.ports import apis
from tasks.ports import persistence


class TestRunSentimentAnalysisJobTask(unittest.TestCase):
  def setUp(self):
    super().setUp()

    self._setup_settings_config_mock()
    self._setup_workflow_exec_loader_mock()
    self._setup_llm_batch_client_mock()
    self._setup_required_task_mock()

  def _setup_settings_config_mock(self):
    self.mock_settings = mock.MagicMock()

    self.enterContext(
        mock.patch(
            "socialpulse_common.config.Settings",
            return_value=self.mock_settings
        )
    )

  def _setup_workflow_exec_loader_mock(self):
    self.mock_workflow_exec_loader = mock.create_autospec(
        persistence.WorkflowExecutionLoaderService, instance=True
    )
    service.registry.register(
        persistence.WorkflowExecutionLoaderService,
        self.mock_workflow_exec_loader
    )

    self.mock_sentiment_data_repo = mock.create_autospec(
        persistence.SentimentDataRepo, instance=True
    )
    service.registry.register(
        persistence.SentimentDataRepo,
        self.mock_sentiment_data_repo
    )

  def _setup_llm_batch_client_mock(self):
    self.mock_llm_client = mock.create_autospec(
        apis.LlmBatchJobApiClient, instance=True
    )
    service.registry.register(apis.LlmBatchJobApiClient, self.mock_llm_client)

  def _setup_required_task_mock(self):
    self.mock_required_task_output = mock.create_autospec(
        tasks_core.SentimentDataRepoTarget, instance=True
    )
    self.mock_required_task_output.table_name = "input_table"

    self.mock_required_task = mock.MagicMock()
    self.mock_required_task.output.return_value = self.mock_required_task_output

  def test_submit_batch_called_with_task_tables(self):
    task = run_sentiment_job.RunSentimentAnalysisJobTask(
        execution_id="test_execution_id",
        my_required_task=self.mock_required_task
    )

    task.run()

    self.mock_llm_client.submit_batch_job.assert_called_once_with(
        input_table_name="input_table",
        output_table_name=task.output().table_name
    )


if __name__ == "__main__":
  unittest.main()
