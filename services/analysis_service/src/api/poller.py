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

This function is triggered on a schedule by Cloud Scheduler via HTTP calls.

Its primary responsibilities are:
1.  Query the database to find workflow executions that are ready to start.
2.  For each ready workflow, trigger its execution via a separate, dedicated
    "Workflow Executor" (WFE) Cloud Function.
3.  Update the workflow's status to 'IN_PROGRESS' to prevent re-processing.
"""

import logging
import os

import fastapi
import google.cloud.logging
from infrastructure.persistence.postgresdb import workflow_data_repo
from infrastructure.triggers import wfe_cloud_function
from infrastructure.triggers import wfe_cloud_run_job
from socialpulse_common import config
from socialpulse_common import service
from socialpulse_common.messages import sentiment_report as report_msg
from socialpulse_common.messages import workflow_execution as wfe
from socialpulse_common.persistence import postgresdb_client as client
from tasks.ports import persistence
from tasks.ports import trigger

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.getLogger().setLevel(log_level)
logger = logging.getLogger(__name__)


app = fastapi.FastAPI()

settings = None
service_registry = None
is_initialized = False


def _bootstrap_services():
  """Initializes and registers all necessary services for the function."""
  global settings, is_initialized, service_registry

  if is_initialized:
    return

  logger.info("Starting service bootstrapping for poller.")
  settings = config.Settings()
  service_registry = service.registry

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

  report_completion_service = (
      wfe_cloud_function.HttpReportCompletionService(
          settings.cloud.report_backend_api_url
      )
  )
  service_registry.register(
      trigger.ReportCompletionService, report_completion_service
  )

  trigger_adapter = wfe_cloud_run_job.CloudJobWorkflowExecutionTrigger(
      project_id=settings.cloud.project_id, region=settings.cloud.region
  )
  service_registry.register(trigger.WorkflowExecutionTrigger, trigger_adapter)

  is_initialized = True
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
    self._mark_completed_trigger: trigger.ReportCompletionService = (
        service.registry.get(trigger.ReportCompletionService)
    )

  def trigger_ready_workflow_execs(self):
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
        self._repo.update_status(exec_id, wfe.Status.IN_PROGRESS)

      except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to process execution_id: %s.", exec_id)

  def mark_completed_reports(self):
    """Finds completed reports and marks them as completed."""
    logger.info("Marking completed reports.")
    completed_report_data = self._repo.find_completed_reports()

    if not completed_report_data:
      logger.info("No completed reports found.")
      return

    logger.info(
        "Found %d completed reports to mark as completed.",
        len(completed_report_data),
    )
    for report_wfes_data in completed_report_data.items():
      report_id = report_wfes_data[0]
      completed_wfes: list[wfe.WorkflowExecutionParams] = report_wfes_data[1]

      try:
        self._mark_report_as_completed(report_id, completed_wfes)
        for workflow in completed_wfes:
          self._repo.update_status(workflow.execution_id, wfe.Status.EXPORTED)
      except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to process report_id: %s.", report_id)

  def _mark_report_as_completed(
      self, report_id: str, wfes: list[wfe.WorkflowExecutionParams]
  ):
    """Marks a report as completed.

    Args:
      report_id: The unique ID of the report to mark as completed.
      wfes: A list of WorkflowExecutionParams associated with the completed
        report.
    """

    def _generate_dataset_uri(execution_id: str):
      """Generates the BigQuery URI for a given execution ID."""
      bq_uri_prefix = (
          f"bq://{settings.cloud.project_id}/{settings.cloud.dataset_name}"
      )
      return f"{bq_uri_prefix}/SentimentDataset_{execution_id}"

    report_datasets: list[report_msg.SentimentReportDataset] = [
        report_msg.SentimentReportDataset(
            report_id=report_id,
            source=wfe_data.source,
            data_output=wfe_data.data_output[0],
            dataset_uri=_generate_dataset_uri(wfe_data.execution_id),
        )
        for wfe_data in wfes
        if wfe_data.data_output
    ]

    logger.info("Marking report %s as completed.", report_id)
    self._mark_completed_trigger.mark_report_completed(
        report_id=report_id, datasets=report_datasets
    )


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
        status_code=500, detail=f"Service initialization failed: {e}"
    ) from e

  try:
    handler = PollerHandler()
    handler.trigger_ready_workflow_execs()
    handler.mark_completed_reports()

    return {"status": "success", "message": "Polling cycle completed."}

  except Exception as e:
    logger.exception("An unexpected error occurred during the polling cycle.")

    raise fastapi.HTTPException(
        status_code=500, detail=f"Polling and triggering failed: {e}"
    ) from e
