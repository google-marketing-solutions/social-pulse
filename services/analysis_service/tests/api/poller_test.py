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
"""Unit tests for the PollerHandler class."""

import unittest
from unittest import mock

from api import poller
from fastapi.testclient import TestClient
from socialpulse_common import service
from socialpulse_common.messages import common as common_msg
from socialpulse_common.messages import workflow_execution as wfe
from tasks.ports import persistence
from tasks.ports import trigger


class PollerHandlerTest(unittest.TestCase):
  """Tests the core logic of the PollerHandler."""

  def setUp(self):  # No MockSettings here
    """Set up mocks for external dependencies for each test."""
    super().setUp()

    self._mock_services()
    self._mock_config_settings()
    self._mock_is_development()

  def _mock_is_development(self):
    patcher = mock.patch("socialpulse_common.config.is_development")
    self.mock_is_dev = patcher.start()
    self.addCleanup(patcher.stop)
    self.mock_is_dev.return_value = False

  def _mock_services(self):
    self.mock_repo = mock.Mock(
        spec=persistence.WorkflowExecutionPersistenceService
    )
    self.mock_repo.find_ready_executions.return_value = []
    self.mock_repo.find_completed_reports.return_value = []

    service.registry.register(
        persistence.WorkflowExecutionPersistenceService, self.mock_repo
    )

    self.mock_trigger = mock.Mock(spec=trigger.WorkflowExecutionTrigger)
    service.registry.register(
        trigger.WorkflowExecutionTrigger, self.mock_trigger
    )

    self.mock_report_completion_trigger = mock.Mock(
        spec=trigger.ReportStatusUpdatingService
    )
    service.registry.register(
        trigger.ReportStatusUpdatingService, self.mock_report_completion_trigger
    )

  def _mock_config_settings(self):
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

    patcher = mock.patch("socialpulse_common.config.Settings")

    self._mock_settings_cls = patcher.start()
    self.addCleanup(patcher.stop)
    self._mock_settings_cls.return_value = self._mock_settings

    # Also patch the module-level settings in api.poller
    patcher_module_settings = mock.patch(
        "api.poller.settings",
        self._mock_settings
    )
    patcher_module_settings.start()
    self.addCleanup(patcher_module_settings.stop)

  def test_trigger_ready_workflow_execs_does_nothing_when_no_ready_workflows(
      self
  ):
    """Tests that no triggers are called if no workflows are found.

    Given no ready workflow executions.
    When the trigger_ready_workflow_execs method is invoked.
    Then no triggers are called, and no status updates are made.
    """
    # Arrange
    self.mock_repo.find_ready_executions.return_value = []

    # Act
    handler = poller.PollerHandler()
    handler.trigger_ready_workflow_execs()

    # Assert
    self.mock_repo.find_ready_executions.assert_called_once()
    self.mock_trigger.trigger_workflow.assert_not_called()
    self.mock_repo.update_status.assert_not_called()

  def test_trigger_ready_workflow_execs_processes_single_ready_workflow(self):
    """Tests that a single ready workflow is triggered and its status updated.

    Given a single ready workflow execution.
    When the trigger_ready_workflow_execs method is invoked.
    Then the workflow is triggered, and its status is updated to IN_PROGRESS.
    """
    # Arrange
    ready_exec = wfe.WorkflowExecutionParams(
        execution_id="exec-123", status=wfe.Status.NEW
    )
    self.mock_repo.find_ready_executions.return_value = [ready_exec]

    # Act
    handler = poller.PollerHandler()
    handler.trigger_ready_workflow_execs()

    # Assert
    self.mock_trigger.trigger_workflow.assert_called_once_with("exec-123")
    self.mock_repo.update_status.assert_called_once_with(
        "exec-123", wfe.Status.IN_PROGRESS
    )

  def test_trigger_ready_workflow_execs_processes_multiple_ready_workflows(
      self
  ):
    """Tests that multiple ready workflows are all triggered and updated.

    Given multiple ready workflow executions.
    When the trigger_ready_workflow_execs method is invoked.
    Then all workflows are triggered, and their statuses are updated to
    IN_PROGRESS.
    """
    # Arrange
    exec1 = wfe.WorkflowExecutionParams(
        execution_id="exec-123", status=wfe.Status.NEW
    )
    exec2 = wfe.WorkflowExecutionParams(
        execution_id="exec-456", status=wfe.Status.NEW
    )
    self.mock_repo.find_ready_executions.return_value = [exec1, exec2]

    # Act
    handler = poller.PollerHandler()
    handler.trigger_ready_workflow_execs()

    # Assert
    self.assertEqual(self.mock_trigger.trigger_workflow.call_count, 2)
    self.mock_trigger.trigger_workflow.assert_any_call("exec-123")
    self.mock_trigger.trigger_workflow.assert_any_call("exec-456")

    self.assertEqual(self.mock_repo.update_status.call_count, 2)
    self.mock_repo.update_status.assert_any_call(
        "exec-123", wfe.Status.IN_PROGRESS
    )
    self.mock_repo.update_status.assert_any_call(
        "exec-456", wfe.Status.IN_PROGRESS
    )

  def test_failure_in_one_workflow_does_not_stop_others(self):
    """Tests other WFE's continue processing even if 1 fails.

    Given multiple ready workflow executions, where one fails to trigger.
    When the trigger_ready_workflow_execs method is invoked.
    Then the failing workflow's trigger attempt is logged, and other
    workflows are still processed.
    """
    # Arrange
    exec1_fail = wfe.WorkflowExecutionParams(
        execution_id="exec-123-fail", status=wfe.Status.NEW
    )
    exec2_ok = wfe.WorkflowExecutionParams(
        execution_id="exec-456-ok", status=wfe.Status.NEW
    )
    self.mock_repo.find_ready_executions.return_value = [exec1_fail, exec2_ok]

    # Make the trigger fail only for the first execution_id
    self.mock_trigger.trigger_workflow.side_effect = [
        Exception("Trigger failed!"),
        None,
    ]

    # Act
    handler = poller.PollerHandler()
    handler.trigger_ready_workflow_execs()

    # Assert that the trigger was attempted for both workflows
    self.assertEqual(self.mock_trigger.trigger_workflow.call_count, 2)

    # Assert that the status was ONLY updated for the successful one
    self.mock_repo.update_status.assert_called_once_with(
        "exec-456-ok", wfe.Status.IN_PROGRESS
    )

  def test_clean_up_staging_datasets_ignores_specific_prefixes(self):
    """Tests that staging cleanup ignores specific dataset prefixes.

    Given a list of staging datasets, some with ignored prefixes.
    When the _clean_up_staging_datasets method is invoked.
    Then only datasets without the ignored prefixes are deleted.
    """
    # Arrange
    mock_dataset_repo = mock.Mock(spec=persistence.SentimentDataRepo)
    service.registry.register(persistence.SentimentDataRepo, mock_dataset_repo)

    mock_dataset_repo.list_datasets_for_execution_id.return_value = [
        "SentimentDataset_123",
        "GenerateJustificationCategoriesTask_123",
        "SomeOtherDataset_123",
        "AnotherDataset_123",
    ]

    exec_params = wfe.WorkflowExecutionParams(
        execution_id="exec-123",
        source=common_msg.SocialMediaSource.YOUTUBE_VIDEO,
        data_output=[common_msg.SentimentDataType.SENTIMENT_SCORE]
    )
    self.mock_repo.find_completed_reports.return_value = {
        "report-123": [exec_params]
    }

    # Act
    handler = poller.PollerHandler()
    handler.mark_completed_reports()

    # Assert
    mock_dataset_repo.list_datasets_for_execution_id.assert_called_once_with(
        "exec-123"
    )
    self.assertEqual(mock_dataset_repo.delete_dataset.call_count, 2)
    mock_dataset_repo.delete_dataset.assert_any_call("SomeOtherDataset_123")
    mock_dataset_repo.delete_dataset.assert_any_call("AnotherDataset_123")

  def test_trigger_ready_workflow_execs_skips_in_development_mode(self):
    """Tests that workflows are NOT triggered when in development mode.

    Given the application is running in development mode.
    When the trigger_ready_workflow_execs method is invoked.
    Then no ready executions are searched for, and no workflows are triggered.
    """
    # Arrange
    self.mock_is_dev.return_value = True

    # Act
    handler = poller.PollerHandler()
    handler.trigger_ready_workflow_execs()

    # Assert
    self.mock_repo.find_ready_executions.assert_not_called()
    self.mock_trigger.trigger_workflow.assert_not_called()

  def test_mark_in_progress_reports_processes_multiple_reports(self):
    """Tests that in-progress reports are correctly marked.

    Given several in-progress report IDs.
    When the mark_in_progress_reports method is invoked.
    Then the mark_report_in_progress trigger is called for each ID.
    """
    # Arrange
    self.mock_repo.find_in_progress_reports.return_value = ["rep-1", "rep-2"]

    # Act
    handler = poller.PollerHandler()
    handler.mark_in_progress_reports()

    # Assert
    self.assertEqual(
        self.mock_report_completion_trigger.mark_report_in_progress.call_count,
        2
    )
    self.mock_report_completion_trigger.mark_report_in_progress.assert_any_call(
        "rep-1"
    )
    self.mock_report_completion_trigger.mark_report_in_progress.assert_any_call(
        "rep-2"
    )

  def test_mark_in_progress_reports_handles_no_reports(self):
    """Tests that no marking occurs if no in-progress reports are found.

    Given no in-progress report IDs.
    When the mark_in_progress_reports method is invoked.
    Then no triggers are called.
    """
    # Arrange
    self.mock_repo.find_in_progress_reports.return_value = []

    # Act
    handler = poller.PollerHandler()
    handler.mark_in_progress_reports()

    # Assert
    (self.mock_report_completion_trigger
     .mark_report_in_progress
     .assert_not_called())

  def test_mark_in_progress_reports_handles_trigger_failure(self):
    """Tests that a failure in one report does not block others.

    Given multiple in-progress report IDs, where one trigger call fails.
    When the mark_in_progress_reports method is invoked.
    Then the failing attempt is caught, and others are still processed.
    """
    # Arrange
    self.mock_repo.find_in_progress_reports.return_value = [
        "fail-rep", "ok-rep"
    ]
    self.mock_report_completion_trigger.mark_report_in_progress.side_effect = [
        Exception("Marking failed!"),
        None,
    ]

    # Act
    handler = poller.PollerHandler()
    handler.mark_in_progress_reports()

    # Assert
    self.assertEqual(
        self.mock_report_completion_trigger.mark_report_in_progress.call_count,
        2
    )
    self.mock_report_completion_trigger.mark_report_in_progress.assert_any_call(
        "ok-rep"
    )


class PollerEndpointTest(unittest.TestCase):
  """Tests the poller FastAPI endpoint."""

  def setUp(self):
    super().setUp()
    self.client = TestClient(poller.app)

  @mock.patch("api.poller._bootstrap_services")
  @mock.patch("api.poller.PollerHandler")
  def test_poller_success(self, mock_handler_cls, mock_bootstrap):
    """Tests the /poller endpoint returns 200 on success.

    Given the application is working correctly.
    When the /poller endpoint is called.
    Then 200 is returned, and bootstrapping and handler methods are called.

    Args:
      mock_handler_cls: Mock class for PollerHandler.
      mock_bootstrap: Mock function for _bootstrap_services.
    """
    # Arrange
    mock_handler = mock.Mock()
    mock_handler_cls.return_value = mock_handler

    # Act
    response = self.client.post("/poller")

    # Assert
    self.assertEqual(response.status_code, 200)
    self.assertEqual(
        response.json(),
        {"status": "success", "message": "Polling cycle completed."},
    )
    mock_bootstrap.assert_called_once()
    mock_handler.trigger_ready_workflow_execs.assert_called_once()
    mock_handler.mark_in_progress_reports.assert_called_once()
    mock_handler.mark_completed_reports.assert_called_once()

  @mock.patch("api.poller._bootstrap_services")
  def test_poller_bootstrap_failure(self, mock_bootstrap):
    """Tests the /poller endpoint returns 500 when bootstrapping fails.

    Given bootstrapping services raises an Exception.
    When the /poller endpoint is called.
    Then a 500 status code is returned with a descriptive error.

    Args:
      mock_bootstrap: Mock function for _bootstrap_services.
    """
    # Arrange
    mock_bootstrap.side_effect = Exception("Bootstrap failed")

    # Act
    response = self.client.post("/poller")

    # Assert
    self.assertEqual(response.status_code, 500)
    self.assertIn("Service initialization failed", response.json()["detail"])

  @mock.patch("api.poller._bootstrap_services")
  @mock.patch("api.poller.PollerHandler")
  def test_poller_handler_failure(self, mock_handler_cls, mock_bootstrap):
    """Tests the /poller endpoint returns 500 when handler fails.

    Given the handler raises an Exception during execution.
    When the /poller endpoint is called.
    Then a 500 status code is returned with a descriptive error.

    Args:
      mock_handler_cls: Mock class for PollerHandler.
      mock_bootstrap: Mock function for _bootstrap_services.
    """
    # Arrange
    mock_handler = mock.Mock()
    mock_handler_cls.return_value = mock_handler
    mock_handler.trigger_ready_workflow_execs.side_effect = Exception(
        "Handler failed"
    )

    # Act
    response = self.client.post("/poller")

    # Assert
    self.assertEqual(response.status_code, 500)
    self.assertIn("Polling and triggering failed", response.json()["detail"])
    mock_bootstrap.assert_called_once()


if __name__ == "__main__":
  unittest.main()
