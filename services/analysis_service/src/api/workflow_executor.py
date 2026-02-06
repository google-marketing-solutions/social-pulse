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

"""HTTP-triggered service that executes a Luigi pipeline for a given execution_id.

This is service is called by the Poller.
Its sole responsibility is to receive a single execution_id, bootstrap all the
necessary services for the data pipeline, and run the long-running Luigi
workflow for that specific ID.

This service is designed for long runtimes on Cloud Run and is not intended
to be called directly by end-users.
"""

import logging
import os
import sys

import google.cloud.logging
from infrastructure.apis import vertexai
from infrastructure.apis import youtube
from infrastructure.persistence.bigquery import sentiment_data_repo
from infrastructure.persistence.postgresdb import workflow_data_repo
import luigi
from socialpulse_common import config
from socialpulse_common import service
from socialpulse_common.messages import workflow_execution as wfe
from socialpulse_common.persistence import postgresdb_client as client
from tasks import execution
from tasks.ports import apis
from tasks.ports import persistence

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.getLogger().setLevel(log_level)
logger = logging.getLogger(__name__)

settings = None
service_registry = None
is_initialized = False


def _bootstrap_services():
  """Initializes and registers all necessary services for the function."""
  global settings, is_initialized, service_registry

  if is_initialized:
    return

  logger.info("Starting service bootstrapping for workflow_executor.")
  settings = config.Settings()
  service_registry = service.registry

  # Bootstrap the WFE persistence service
  postgres_client = client.PostgresDbClient(
      host=settings.db.host,
      port=settings.db.port,
      database=settings.db.name,
      user=settings.db.username,
      password=settings.db.password,
  )
  workflow_repo = (
      workflow_data_repo.
          PostgresDbWorkflowExecutionPersistenceService(postgres_client)
  )
  service_registry.register(
      persistence.WorkflowExecutionPersistenceService,
      workflow_repo,
  )

  # Bootstrap the sentiment data repo
  bq_repo = sentiment_data_repo.BigQuerySentimentDataRepo(
      gcp_project_id=settings.cloud.project_id,
      bq_dataset_name=settings.cloud.dataset_name,
  )
  service.registry.register(persistence.SentimentDataRepo, bq_repo)

  # Bootstrap the YT and Vertext AI API client
  yt_api = youtube.YoutubeApiHttpClient(api_key=settings.api.youtube.key)
  vertex_api = vertexai.VertexAiLlmBatchJobApiClient(
      project_id=settings.cloud.project_id,
      region=settings.cloud.region,
      bq_dataset_name=settings.cloud.dataset_name,
  )
  service.registry.register(apis.YoutubeApiClient, yt_api)
  service.registry.register(apis.LlmBatchJobApiClient, vertex_api)

  is_initialized = True


class PipelineRunner:
  """Handles the core logic of running a single Luigi pipeline."""

  def run(self, execution_id: str) -> luigi.execution_summary.LuigiRunResult:
    """Configures the environment and executes the Luigi pipeline."""

    logger.info("Invoking luigi.build for execution_id: %s", execution_id)
    run_result = luigi.build([
        execution.WorkflowExecution(execution_id=execution_id)
    ], detailed_summary=True, local_scheduler=True)
    return run_result

  def mark_as_failed(self, execution_id: str):
    """Marks the workflow execution as FAILED in the database."""
    try:
      self._config.workflow_repo.update_status(execution_id, wfe.Status.FAILED)
    except Exception as cleanup_error:  # pylint: disable=broad-exception-caught
      logger.error(
          "Failed to mark job as FAILED during cleanup for execution_id %s: %s",
          execution_id,
          cleanup_error,
      )


def main():
  """Executes the Luigi pipeline for the given execution_id."""
  if len(sys.argv) < 2:
    logger.error("An execution ID was not provided")
    raise ValueError("No execution ID provided to the executor.")

  execution_id = sys.argv[1]
  runner = None

  try:
    _bootstrap_services()

    runner = PipelineRunner()
    run_result = runner.run(execution_id)

    if run_result.status not in (
        luigi.LuigiStatusCode.SUCCESS,
        luigi.LuigiStatusCode.SUCCESS_WITH_RETRY,
    ):
      logger.error(
          "Luigi pipeline FAILED for execution_id: %s.\n%s", execution_id,
          run_result.summary_text
      )
      runner.mark_as_failed(execution_id)

    logger.info("Luigi pipeline succeeded for execution_id: %s.", execution_id)

  except Exception:  # pylint: disable=broad-exception-caught
    logger.exception(
        "Critical error occurred in the workflow executor for execution_id: %s",
        execution_id,
    )
    if runner:
      runner.mark_as_failed(execution_id)
    raise


if __name__ == "__main__":
  main()
