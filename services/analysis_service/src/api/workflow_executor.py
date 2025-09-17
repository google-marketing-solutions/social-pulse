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


log_format = (
    "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format=log_format)
logger = logging.getLogger(__name__)

settings = config.Settings()


class AppConfig:
  """Handles service bootstrapping."""

  def __init__(self):
    logger.info("Initializing AppConfig for Workflow Executor...")

    self.postgres_client = client.PostgresDbClient(
        host=settings.db.host,
        port=settings.db.port,
        database=settings.db.name,
        user=settings.db.username,
        password=settings.db.password,
    )
    self.workflow_repo = (
        workflow_data_repo.PostgresDbWorkflowExecutionPersistenceService(
            self.postgres_client
        )
    )
    self.bq_repo = sentiment_data_repo.BigQuerySentimentDataRepo(
        gcp_project_id=settings.cloud.project_id,
        bq_dataset_name=settings.cloud.dataset_name,
    )

    self.yt_api = youtube.YoutubeApiHttpClient(api_key=settings.api.youtube.key)
    self.vertex_api = vertexai.VertexAiLlmBatchJobApiClient(
        project_id=settings.cloud.project_id,
        region=settings.cloud.region,
        bq_dataset_name=settings.cloud.dataset_name,
    )
    logger.info("AppConfig initialized successfully.")


class PipelineRunner:
  """Handles the core logic of running a single Luigi pipeline."""

  def __init__(self, runner_config: AppConfig):
    self._config = runner_config

  def _register_services_for_pipeline(self):
    """Registers all necessary services into the global service registry."""
    logger.info("Registering services for Luigi pipeline...")
    service.registry.register(
        persistence.WorkflowExecutionPersistenceService,
        self._config.workflow_repo,
    )
    service.registry.register(
        persistence.SentimentDataRepo, self._config.bq_repo
    )
    service.registry.register(apis.YoutubeApiClient, self._config.yt_api)
    service.registry.register(
        apis.LlmBatchJobApiClient, self._config.vertex_api
    )

  def run(self, execution_id: str) -> luigi.execution_summary.LuigiRunResult:
    """Configures the environment and executes the Luigi pipeline."""
    self._register_services_for_pipeline()
    logger.info("Invoking luigi.build for execution_id: %s", execution_id)
    run_result = luigi.build(
        [execution.WorkflowExecution(execution_id=execution_id)],
        detailed_summary=True,
        local_scheduler=False,
        scheduler_host=settings.cloud.task_scheduler_host,
        scheduler_port=settings.cloud.task_scheduler_port,
    )
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


app_config = AppConfig()


def main():
  """Executes the Luigi pipeline for the given execution_id."""
  if len(sys.argv) < 2:
    logger.error("An execution ID was not provided")
    sys.exit(1)

  execution_id = sys.argv[1]
  try:
    runner = PipelineRunner(app_config)
    run_result = runner.run(execution_id)

    if run_result.status not in (
        luigi.LuigiStatusCode.SUCCESS,
        luigi.LuigiStatusCode.SUCCESS_WITH_RETRY,
    ):
      logger.error(
          "Luigi pipeline FAILED for execution_id: %s.\n%s",
          execution_id,
          run_result.summary_text
      )
      runner.mark_as_failed(execution_id)
      sys.exit(1)

    logger.info("Luigi pipeline succeeded for execution_id: %s.", execution_id)

  except Exception:  # pylint: disable=broad-exception-caught
    logger.exception(
        "Critical error occurred in the workflow executor for execution_id: %s",
        execution_id,
    )
    # For any other unexpected crash
    if runner:
      runner.mark_as_failed(execution_id)
    sys.exit(1)


if __name__ == "__main__":
  main()
