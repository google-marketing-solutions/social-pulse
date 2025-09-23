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

import fastapi
from infrastructure.persistence.postgresdb import workflow_data_repo
from infrastructure.triggers import wfe_cloud_run_job
from socialpulse_common import config
from socialpulse_common import service
from socialpulse_common.persistence import postgresdb_client as client
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


app = fastapi.FastAPI()


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
  trigger_adapter = wfe_cloud_run_job.CloudJobWorkflowExecutionTrigger(
      project_id=settings.cloud.project_id,
      region=settings.cloud.region
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
      except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to process execution_id: %s.", exec_id)


@app.post("/poller")
def poller(request: fastapi.Request):  # pylint: disable=unused-argument
  """Cloud Scheduler HTTP endpoint to initiate the poller cycle.

  This endpoint is triggered by an authenticated HTTP POST request
  from the Cloud Scheduler service.

  Args:
    request: The incoming FastAPI request object.

  Returns:
    A dictionary with a status and message indicating the outcome of the
    polling cycle.
  """
  try:
    _bootstrap_services()
  except Exception as e:
    logger.exception(
        "Critical error during service bootstrapping. Aborting run."
    )
    raise fastapi.HTTPException(
        status_code=500,
        detail=f"Service initialization failed: {e}"
    ) from e

  try:
    handler = PollerHandler()
    handler.poll_and_trigger()

    return {"status": "success", "message": "Polling cycle completed."}

  except Exception as e:
    logger.exception("An unexpected error occurred during the polling cycle.")
    # CRITICAL FIX: Raise 500 to signal the job failed and trigger retries
    raise fastapi.HTTPException(
        status_code=500,
        detail=f"Polling and triggering failed: {e}"
    ) from e
