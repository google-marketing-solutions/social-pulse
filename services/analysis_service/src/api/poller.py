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
"""Scheduler-triggered Cloud Function to poll for and trigger new workflows.

This function is triggered on a schedule by Cloud Scheduler via Pub/Sub.

Its primary responsibilities are:
1.  Query the database to find workflow executions that are ready to start.
2.  For each ready workflow, trigger its execution via a separate, dedicated
    "Workflow Executor" (WFE) Cloud Function.
3.  Update the workflow's status to 'IN_PROGRESS' to prevent re-processing.
"""

import logging
import os

import functions_framework

from infrastructure.persistence.postgresdb import client
from infrastructure.persistence.postgresdb import workflow_data_repo
from infrastructure.triggers import wfe_cloud_function
from socialpulse_common import config
from socialpulse_common import service
from socialpulse_common.messages import workflow_execution as wfe
from tasks.ports import persistence
from tasks.ports import trigger


log_format = (
    "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format=log_format)
logger = logging.getLogger(__name__)

try:
  settings = config.Settings()
  service_registry = service.registry
  _is_initialized = False
except Exception as e:  # pylint: disable=broad-exception-caught
  logger.critical(
      "FATAL: Could not initialize settings on cold start. Error: %s", e
  )
  settings = None
  _is_initialized = False


def _bootstrap_services():
  """Initializes and registers all necessary services for the function."""
  global _is_initialized
  if _is_initialized:
    return

  if not settings:
    raise RuntimeError(
        "Cannot bootstrap services because Settings failed to initialize."
    )

  logger.info("Starting service bootstrapping for poller.")

  postgres_client = client.PostgresDbClient(
      host=settings.db.host,
      port=settings.db.port,
      database=settings.db.name,
      user=settings.db.username,
      password=settings.db.password,
  )
  workflow_repo_adapter = (
      workflow_data_repo.PostgresDbWorkflowExecutionPersistenceService(
          postgres_client
      )
  )
  service_registry.register(
      persistence.WorkflowExecutionPersistenceService, workflow_repo_adapter
  )

  # Register Workflow Trigger Service
  trigger_adapter = wfe_cloud_function.HttpWorkflowExecutionTrigger(
      trigger_url=settings.cloud.wfe_trigger_url
  )
  service_registry.register(trigger.WorkflowExecutionTrigger, trigger_adapter)

  _is_initialized = True
  logger.info("Service bootstrapping complete.")


class PollerHandler:
  """Handles the logic of a single polling and triggering cycle."""

  def __init__(self):
    """Initializes the handler by retrieving dependencies from the registry."""
    self._repo: persistence.WorkflowExecutionPersistenceService = (
        service.registry.get(persistence.WorkflowExecutionPersistenceService)
    )
    self._trigger: trigger.WorkflowExecutionTrigger = service.registry.get(
        trigger.WorkflowExecutionTrigger
    )

  def poll_and_trigger(self):
    """Finds ready workflows, triggers them, and updates their status."""
    logger.info("Polling for ready workflow executions.")
    ready_executions = self._repo.find_ready_executions()

    if not ready_executions:
      logger.info("No ready workflows found.")
      return

    logger.info("Found %d ready workflows to trigger.", len(ready_executions))

    for execution in ready_executions:
      exec_id = execution.execution_id
      try:
        logger.info("Triggering workflow for execution_id: %s", exec_id)
        self._trigger.trigger_workflow(exec_id)

        logger.info(
            "Updating status to IN_PROGRESS for execution_id: %s", exec_id
        )
        self._repo.update_status(exec_id, wfe.Status.IN_PROGRESS)
      except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to process execution_id: %s.", exec_id)


@functions_framework.cloud_event
def poller(cloud_event):  # pylint: disable=unused-argument
  """Scheduler-triggered Cloud Function that acts as the main entry point.

  Args:
      cloud_event: The CloudEvent object representing the trigger. This is
      required by the functions-framework for Pub/Sub triggers, but its
      contents are not used in this function.
  """
  try:
    _bootstrap_services()
  except Exception:  # pylint: disable=broad-exception-caught
    logger.exception(
        "Critical error during service bootstrapping. Aborting run."
    )
    return

  try:
    handler = PollerHandler()
    handler.poll_and_trigger()
  except Exception:  # pylint: disable=broad-exception-caught
    logger.exception("An unexpected error occurred during the polling cycle.")
