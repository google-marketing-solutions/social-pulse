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
"""Unit tests for the workflow_executor module."""

import unittest
from unittest import mock

from api import workflow_executor
from infrastructure.apis import vertexai
from infrastructure.apis import youtube
import luigi
from socialpulse_common import config
from socialpulse_common import service
from socialpulse_common.messages import workflow_execution as wfe
from socialpulse_common.persistence import postgresdb_client as client
from tasks.ports import apis
from tasks.ports import persistence


class PipelineRunnerTest(unittest.TestCase):
  """Tests the PipelineRunner class."""

  def setUp(self):
    """Sets up the test environment."""
    super().setUp()

    self.runner = workflow_executor.PipelineRunner()

    self.mock_workflow_repo = mock.Mock(
        spec=persistence.WorkflowExecutionPersistenceService
    )
    service.registry.register(
        persistence.WorkflowExecutionPersistenceService, self.mock_workflow_repo
    )

  @mock.patch("luigi.build")
  def test_run(self, mock_luigi_build):
    """Tests that the luigi pipeline is built and run.

    Given a PipelineRunner instance.
    When the run method is called.
    Then the luigi.build function is called with the correct parameters.

    Args:
      mock_luigi_build: Mock object for luigi.build.
    """
    # Act
    self.runner.run("test_execution_id")

    # Assert
    mock_luigi_build.assert_called_once()
    self.assertEqual(
        mock_luigi_build.call_args[0][0][0].execution_id, "test_execution_id"
    )

  def test_mark_as_failed(self):
    """Tests that the workflow execution is marked as failed.

    Given a PipelineRunner instance.
    When the mark_as_failed method is called.
    Then the workflow repo's update_status method is called with FAILED.
    """
    # Act
    self.runner.mark_as_failed("test_execution_id")

    # Assert
    self.mock_workflow_repo.update_status.assert_called_once_with(
        "test_execution_id", wfe.Status.FAILED
    )


class WorkflowExecutorTest(unittest.TestCase):
  """Tests the workflow_executor module."""

  def setUp(self):
    """Sets up the test environment."""
    super().setUp()

    self._mock_config_settings()
    self._mock_postgres_client()
    self._mock_youtube_client()
    self._mock_vertexai_client()

  def tearDown(self):
    """Tears down the test environment."""
    super().tearDown()
    service.registry._registered_services.clear()

  def _mock_config_settings(self):
    """Mocks configuration settings."""
    self._mock_settings = mock.Mock()
    self._mock_settings.db.host = "test_db_host"
    self._mock_settings.db.port = 1234
    self._mock_settings.db.name = "test_db_name"
    self._mock_settings.db.username = "test_db_user"
    self._mock_settings.db.password = "test_db_password"
    self._mock_settings.api.youtube.key = "test_yt_key"
    self._mock_settings.cloud.project_id = "test_project_id"
    self._mock_settings.cloud.region = "test_region"
    self._mock_settings.cloud.dataset_name = "test_dataset_name"

    patcher = mock.patch.object(config, "Settings")
    self._mock_settings_cls = patcher.start()
    self.addCleanup(patcher.stop)
    self._mock_settings_cls.return_value = self._mock_settings

  def _mock_postgres_client(self):
    """Mocks the PostgresDbClient."""
    patcher = mock.patch.object(client, "PostgresDbClient")
    self.mock_postgres_client_cls = patcher.start()
    self.addCleanup(patcher.stop)

  def _mock_youtube_client(self):
    """Mocks the YoutubeApiHttpClient."""
    patcher = mock.patch.object(youtube, "YoutubeApiHttpClient")
    self.mock_youtube_client_cls = patcher.start()
    self.addCleanup(patcher.stop)

  def _mock_vertexai_client(self):
    """Mocks the VertexAiLlmBatchJobApiClient."""
    patcher = mock.patch.object(vertexai, "VertexAiLlmBatchJobApiClient")
    self.mock_vertexai_client_cls = patcher.start()
    self.addCleanup(patcher.stop)

  def test_bootstrap_services(self):
    """Tests that the _bootstrap_services function works correctly.

    Given a clean service registry.
    When the _bootstrap_services function is called.
    Then the settings are loaded, clients are instantiated, and services are
    registered.
    """
    # Arrange
    workflow_executor.is_initialized = False

    # Act
    workflow_executor._bootstrap_services()

    # Assert
    self._mock_settings_cls.assert_called_once()
    self.mock_postgres_client_cls.assert_called_once_with(
        host="test_db_host",
        port=1234,
        database="test_db_name",
        user="test_db_user",
        password="test_db_password",
    )
    self.mock_youtube_client_cls.assert_called_once_with(api_key="test_yt_key")
    self.mock_vertexai_client_cls.assert_called_once_with(
        project_id="test_project_id",
        region="test_region",
        bq_dataset_name="test_dataset_name",
    )
    self.assertIsNotNone(
        service.registry.get(persistence.WorkflowExecutionPersistenceService)
    )
    self.assertIsNotNone(service.registry.get(persistence.SentimentDataRepo))
    self.assertIsNotNone(service.registry.get(apis.YoutubeApiClient))
    self.assertIsNotNone(service.registry.get(apis.LlmBatchJobApiClient))

  @mock.patch("api.workflow_executor.PipelineRunner")
  @mock.patch("sys.argv", ["", "test_execution_id"])
  def test_main_success(self, mock_pipeline_runner):
    """Tests the main function for a successful pipeline execution.

    Given a successful Luigi pipeline run.
    When the main function is called.
    Then the pipeline is run and no errors are raised.

    Args:
      mock_pipeline_runner: Mock object for PipelineRunner.
    """
    # Arrange
    workflow_executor.is_initialized = True  # Prevent bootstrap from running
    mock_run_result = mock.Mock()
    mock_run_result.status = luigi.LuigiStatusCode.SUCCESS
    mock_pipeline_runner.return_value.run.return_value = mock_run_result

    # Act & Assert
    workflow_executor.main()
    mock_pipeline_runner.return_value.run.assert_called_once_with(
        "test_execution_id"
    )
    mock_pipeline_runner.return_value.mark_as_failed.assert_not_called()

  @mock.patch("api.workflow_executor.PipelineRunner")
  @mock.patch("sys.argv", ["", "test_execution_id"])
  def test_main_pipeline_failure(self, mock_pipeline_runner):
    """Tests the main function for a failed pipeline execution.

    Given a failed Luigi pipeline run.
    When the main function is called.
    Then the pipeline is run and the execution is marked as failed.

    Args:
      mock_pipeline_runner: Mock object for PipelineRunner.
    """
    # Arrange
    workflow_executor.is_initialized = True
    mock_run_result = mock.Mock()
    mock_run_result.status = luigi.LuigiStatusCode.FAILED
    mock_pipeline_runner.return_value.run.return_value = mock_run_result

    # Act
    workflow_executor.main()

    # Assert
    mock_pipeline_runner.return_value.run.assert_called_once_with(
        "test_execution_id"
    )
    mock_pipeline_runner.return_value.mark_as_failed.assert_called_once_with(
        "test_execution_id"
    )

  @mock.patch("api.workflow_executor.PipelineRunner")
  @mock.patch("sys.argv", ["", "test_execution_id"])
  def test_main_critical_error(self, mock_pipeline_runner):
    """Tests the main function for a critical error during execution.

    Given a critical error during pipeline execution.
    When the main function is called.
    Then the exception is caught, the execution is marked as failed, and the
    exception is re-raised.

    Args:
      mock_pipeline_runner: Mock object for PipelineRunner.
    """
    # Arrange
    workflow_executor.is_initialized = True
    mock_pipeline_runner.return_value.run.side_effect = Exception(
        "Critical error"
    )

    # Act & Assert
    with self.assertRaises(Exception):
      workflow_executor.main()

    mock_pipeline_runner.return_value.run.assert_called_once_with(
        "test_execution_id"
    )
    mock_pipeline_runner.return_value.mark_as_failed.assert_called_once_with(
        "test_execution_id"
    )

  @mock.patch("sys.argv", [""])
  def test_main_no_execution_id(self):
    """Tests that the script raises an error if no execution ID is provided.

    Given no execution ID is provided in the command line arguments.
    When the main function is called.
    Then a ValueError is raised.
    """
    # Act & Assert
    with self.assertRaises(ValueError):
      workflow_executor.main()


if __name__ == "__main__":
  unittest.main()
