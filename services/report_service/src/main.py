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
from socialpulse_common import config
from socialpulse_common.messages import sentiment_report as report_msg
from socialpulse_common.persistence import postgresdb_client as client


log_level = os.environ.get("LOG_LEVEL", "DEBUG").upper()
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

    self.sentiment_report_repository: persistence.SentimentReportRepository = (
        sentiment_report_repo.PostgresDbSentimentReportRepo(postgres_client)
    )

    logger.info(
        "Setting up WFE trigger client with URL:  %s",
        settings.cloud.workflow_runner_api_url
    )
    self.wfe_service = wfe_service_lib.HttpEndpoingWorkflowExecutionService(
        settings.cloud.workflow_runner_api_url
    )


FastAPI = fastapi.FastAPI
app = FastAPI()
app_config = AppConfig()


@app.get("/api/hello")
def read_root():
  return {"message": "Hello from the backend!"}


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

    app_config.wfe_service.trigger_run_report(report)
    return report

  except Exception as e:  # pylint: disable=broad-except
    new_report_entity.mark_as_failed(str(e))
    app_config.sentiment_report_repository.persist_report(new_report_entity)
    logger.exception("Error occurred, will return 500 error:")

    raise fastapi.HTTPException(
        status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
    ) from e


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
    report_entity = app_config.sentiment_report_repository.load_report(
        report_id
    )
    report_entity.mark_as_completed(datasets)
    app_config.sentiment_report_repository.persist_report(report_entity)

    return report_entity
  except Exception as e:  # pylint: disable=broad-except
    logger.exception("Error occurred, will return 500 error:")

    raise fastapi.HTTPException(
        status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
    ) from e


@app.get("/api/report/{report_id}")
def get_report(report_id: str) -> report_msg.SentimentReport:
  """Retrieves a sentiment report by its ID."""
  try:
    report = app_config.sentiment_report_repository.load_report(report_id)
    return report
  except ValueError as e:
    raise fastapi.HTTPException(
        status_code=fastapi.status.HTTP_404_NOT_FOUND, detail=str(e)
    ) from e
  except Exception as e:  # pylint: disable=broad-except
    logger.exception("Error occurred, will return 500 error:")
    raise fastapi.HTTPException(
        status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
    ) from e
