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
"""Mixins for tests related to sentiment tasks."""
from unittest import mock

import luigi
from socialpulse_common import service
from socialpulse_common.messages import workflow_execution as wfe
from tasks import core as tasks_core
from tasks.ports import persistence


class SetupMockSentimentTaskDepependenciesMixin():
  """A mixin class to set up mock dependencies for sentiment-related tasks.

  This mixin provides methods to mock the workflow parameters loader,
  the sentiment data repository, and a required upstream task.

  Properties created by this mixin for use in child classes:

  - `mock_wfe_params_loader_service`: A mock of
      `persistence.WorkflowExecutionLoaderService`.
  - `mock_execution_params`: A mock of `wfe.WorkflowExecutionParams`.
  - `mock_sentiment_data_repo`: A mock of `persistence.SentimentDataRepo`.
  - `mock_required_task`: A mock of a required upstream `luigi.Task`.
  - `mock_input_target`: A mock of the output target of the required task.
  """

  def setup_all_mock_dependencies(self):
    self.setup_mock_workflow_params()
    self.setup_mock_setniment_data_repo()
    self.setup_mock_required_task()
    self.setup_mock_config()

  def setup_mock_config(self):
    """Sets up a mock Settings object."""
    self.mock_settings_patcher = mock.patch(
        "socialpulse_common.config.Settings"
    )
    self.mock_settings_cls = self.mock_settings_patcher.start()
    self.addCleanup(self.mock_settings_patcher.stop)

    self.mock_settings = mock.Mock()
    self.mock_settings_cls.return_value = self.mock_settings

    # Set up default values for settings
    self.mock_settings.cloud.project_id = "test_project_id"
    self.mock_settings.cloud.region = "us-central1"
    self.mock_settings.api.youtube.key = "test_api_key"

  def setup_mock_workflow_params(self):
    """Sets up a mock WorkflowExecutionLoaderService."""
    self.mock_wfe_params_loader_service = mock.Mock(
        spec=persistence.WorkflowExecutionPersistenceService
    )
    self.mock_execution_params = mock.Mock(spec=wfe.WorkflowExecutionParams)
    self.mock_wfe_params_loader_service.load_execution.return_value = (
        self.mock_execution_params
    )
    service.registry.register(
        persistence.WorkflowExecutionPersistenceService,
        self.mock_wfe_params_loader_service
    )

  def setup_mock_setniment_data_repo(self):
    """Sets up a mock SentimentDataRepo."""
    self.mock_sentiment_data_repo = mock.Mock(
        spec=persistence.SentimentDataRepo
    )
    service.registry.register(
        persistence.SentimentDataRepo,
        self.mock_sentiment_data_repo
    )

  def setup_mock_required_task(self):
    """Sets up a mock required Luigi task."""
    # Need to clear Luigi's task cache, otherwise it'll re-use whatever test
    # child task created by the first executed test.
    luigi.Task.clear_instance_cache()

    self.mock_input_target = mock.Mock(
        spec=tasks_core.SentimentDataRepoTarget
    )
    self.mock_input_target.table_name = (
        "SomeTaskName_mock_input_dataset"
    )
    self.mock_input_target.exists.return_value = True

    self.mock_required_task = mock.Mock(spec=luigi.Task)
    self.mock_required_task.requires.return_value = []
    self.mock_required_task.output.return_value = (
        self.mock_input_target
    )
