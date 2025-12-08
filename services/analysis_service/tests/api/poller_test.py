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
from socialpulse_common import service
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

  def _mock_services(self):
    self.mock_repo = mock.Mock(
        spec=persistence.WorkflowExecutionPersistenceService
    )
    service.registry.register(
        persistence.WorkflowExecutionPersistenceService, self.mock_repo
    )

    self.mock_trigger = mock.Mock(spec=trigger.WorkflowExecutionTrigger)
    service.registry.register(
        trigger.WorkflowExecutionTrigger, self.mock_trigger
    )

    self.mock_report_completion_trigger = mock.Mock(
        spec=trigger.ReportCompletionService
    )
    service.registry.register(
        trigger.ReportCompletionService, self.mock_report_completion_trigger
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


if __name__ == "__main__":
  unittest.main()
