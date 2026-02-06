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

"""Module for report service HTTP endpoint."""

import logging
import os

from domain import sentiment_report
from domain.ports import persistence
import fastapi

from infrastructure.api.http import workflow_execution_service as wfe_service_lib
from infrastructure.persistence.postgresdb import sentiment_report_repo
from infrastructure.persistence.postgresdb import sentiment_report_search_repo
from socialpulse_common import config
from socialpulse_common.messages import sentiment_report as report_msg
from socialpulse_common.persistence import postgresdb_client as client
from socialpulse_common.persistence import bigquery_client
from infrastructure.bigquery.dataset import bq_dataset_repo

log_level = os.environ.get("LOG_LEVEL", "DEBUG").upper()
logging.basicConfig(level=log_level)
logging.getLogger().setLevel(log_level)
logger = logging.getLogger(__name__)

settings = config.Settings()


class AppConfig:
  """Application configuration."""

  def __init__(self) -> None:
    postgres_client = client.PostgresDbClient(
        host=settings.db.host,
        port=settings.db.port,
        database=settings.db.name,
        user=settings.db.username,
        password=settings.db.password,
    )

    self.sentiment_report_repository: persistence.SentimentReportRepo = (
        sentiment_report_repo.PostgresDbSentimentReportRepo(postgres_client)
    )
    self.sentiment_report_search_repository: (
        persistence.SentimentReportSearchRepo
    ) = sentiment_report_search_repo.PostgresDbSentimentReportSearchRepo(
        postgres_client
    )

    logger.info(
        "Setting up WFE trigger client with URL:  %s",
        settings.cloud.workflow_runner_api_url,
    )
    self.wfe_service = wfe_service_lib.HttpEndpoingWorkflowExecutionService(
        settings.cloud.workflow_runner_api_url
    )

    self.bq_client = bigquery_client.BigQueryClient()
    self.dataset_repository = bq_dataset_repo.BigQueryDatasetRepo(
        self.bq_client
    )


FastAPI = fastapi.FastAPI
app = FastAPI()
app_config = AppConfig()


@app.get("/api/hello")
def read_root():
  return {"message": "Hello from the backend!"}


@app.get("/api/reports")
def list_reports(
    status: report_msg.Status = None,
    topic: str = None,
) -> list[report_msg.SentimentReport]:
  """Lists sentiment reports matching the provided criteria.

  Args:
    status: Optional status to filter by.
    topic: Optional topic substring to filter by.

  Returns:
    A list of sentiment reports.
  """
  try:
    criteria = persistence.SentimentReportSearchCriteria(
        status=status, topic_contains=topic
    )

    return app_config.sentiment_report_search_repository.get_reports(criteria)
  except Exception as e:
    logger.exception("Error listing reports:")
    raise fastapi.HTTPException(
        status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    ) from e


@app.post("/api/report")
def create_report(
    report: report_msg.SentimentReport,
) -> report_msg.SentimentReport:  # pyformat: disable
  """Creates a new sentiment report.

  Args:
    report: The sentiment report message containing the details for the new
      report.

  Returns:
    The created sentiment report message with its assigned ID and timestamps.
  """
  try:
    logger.info("Creating report with the following details: %s", report)
    new_report_entity = (
        sentiment_report.SentimentReportEntity.create_sentiment_report(
            topic=report.topic,
            sources=report.sources,
            data_output=report.data_output,
            start_time=report.start_time,
            end_time=report.end_time,
            include_justifications=report.include_justifications,
        )
    )

    app_config.sentiment_report_repository.persist_report(new_report_entity)

    report.report_id = new_report_entity.entity_id
    report.created_on = new_report_entity.created
    report.last_updated_on = new_report_entity.last_updated
    # Ensure status is populated for response
    report.status = new_report_entity.status

    app_config.wfe_service.trigger_run_report(report)
    return report

  except Exception as e:  # pylint: disable=broad-except
    if "new_report_entity" in locals():
      new_report_entity.mark_as_failed(str(e))
      app_config.sentiment_report_repository.persist_report(new_report_entity)
    logger.exception("Error occurred, will return 500 error:")

    raise fastapi.HTTPException(
        status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    ) from e


def _entity_to_message(
    entity: sentiment_report.SentimentReportEntity,
) -> report_msg.SentimentReport:
  """Converts a SentimentReportEntity to a SentimentReport message."""
  return report_msg.SentimentReport(
      report_id=entity.entity_id,
      created_on=entity.created,
      last_updated_on=entity.last_updated,
      topic=entity.topic,
      status=entity.status,
      sources=entity.sources,
      data_output=entity.data_outputs[0] if entity.data_outputs else None,
      start_time=entity.start_time,
      end_time=entity.end_time,
      include_justifications=entity.include_justifications,
      datasets=entity.datasets,
      # These fields might need to be populated if available in entity
      report_artifact_type=getattr(
          entity,
          "report_artifact_type",
          report_msg.ReportArtifactType.BQ_TABLE,
      ),
      report_artifact_uri=getattr(entity, "report_artifact_uri", None),
      # Manually attach analysis results if they were dynamically added to
      # entity
      analysis_results=getattr(entity, "analysis_results", None),
  )


@app.post("/api/{report_id}/mark_as_completed")
def mark_as_completed(
    report_id: str, datasets: list[report_msg.SentimentReportDataset]
) -> report_msg.SentimentReport:
  """Marks a sentiment report as completed and associates datasets with it.

  Args:
    report_id: The ID of the report to mark as completed.
    datasets: A list of SentimentReportDataset messages containing information
      about the generated datasets.
  """
  try:
    logger.info(
        "Marking report %s as completed with %d datasets",
        report_id,
        len(datasets),
    )
    report_entity = app_config.sentiment_report_repository.load_report(
        report_id
    )

    report_entity.mark_as_completed(datasets)
    app_config.sentiment_report_repository.persist_report(report_entity)

    return _entity_to_message(report_entity)

  except Exception as e:  # pylint: disable=broad-except
    logger.exception("Error occurred, will return 500 error:")

    raise fastapi.HTTPException(
        status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    ) from e


@app.get("/api/report/{report_id}")
def get_report(report_id: str) -> report_msg.SentimentReport:
  """Retrieves a sentiment report by its ID."""
  try:
    report_entity = app_config.sentiment_report_repository.load_report(
        report_id
    )

    # If report is completed, try to fetch analysis results from BigQuery
    if (
        report_entity.status == report_msg.Status.COMPLETED
        and report_entity.datasets
    ):
      try:
        report_entity.analysis_results = (
            app_config.dataset_repository.get_analysis_results(
                report_entity.datasets
            )
        )
      except Exception as e:
        logger.warning(
            f"Failed to fetch analysis results for report {report_id}: {e}"
        )
        # Fail gracefully? Or partial result?
        # Proceeding with valid report entity but potentially missing results.

    return _entity_to_message(report_entity)
  except ValueError as e:
    raise fastapi.HTTPException(
        status_code=fastapi.status.HTTP_404_NOT_FOUND, detail=str(e)
    ) from e
  except Exception as e:  # pylint: disable=broad-except
    logger.exception("Error occurred, will return 500 error:")
    raise fastapi.HTTPException(
        status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    ) from e
