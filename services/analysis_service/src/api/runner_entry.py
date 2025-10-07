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
"""Module for the Runner service HTTP endpoint using FastAPI.

This service acts as the primary API endpoint for the Analytic Service. Its main
responsibility is to de-aggregate high-level report requests into specific,
persisted workflow execution jobs.
"""

import datetime
import logging
import os
import uuid
import fastapi

from infrastructure.persistence.postgresdb import workflow_data_repo
from socialpulse_common import config
from socialpulse_common.messages import common as common_msg
from socialpulse_common.messages import sentiment_report as report_msg
from socialpulse_common.messages import workflow_execution as wfe
from socialpulse_common.persistence import postgresdb_client as client
from tasks.ports import persistence

log_format = (
    "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s")
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format=log_format)
logger = logging.getLogger(__name__)

settings = config.Settings()


class AppConfig:
  """Handles service bootstrapping and holds dependency instances."""

  def __init__(self):
    logger.info("Initializing AppConfig and bootstrapping services.")
    postgres_client = client.PostgresDbClient(
        host=settings.db.host,
        port=settings.db.port,
        database=settings.db.name,
        user=settings.db.username,
        password=settings.db.password,
    )
    self.workflow_repo: persistence.WorkflowExecutionPersistenceService = (
        workflow_data_repo.PostgresDbWorkflowExecutionPersistenceService(
            postgres_client))
    logger.info("AppConfig initialized successfully.")


class Deaggregator:
  """Handles the logic of processing a single de-aggregation request."""

  def __init__(self,
               workflow_repo: persistence.WorkflowExecutionPersistenceService):
    self._workflow_repo = workflow_repo

  def create_workflows(
      self,
      report: report_msg.SentimentReport,
  ) -> dict[str, str]:
    """Creates and persists workflow records, ensuring dependencies are met."""
    created_workflows = {}
    video_execution_id = None

    needs_video_workflow = (
        common_msg.SocialMediaSource.YOUTUBE_VIDEO in report.sources
        or common_msg.SocialMediaSource.YOUTUBE_COMMENT in report.sources)

    if needs_video_workflow:
      video_params = wfe.WorkflowExecutionParams(
          source=common_msg.SocialMediaSource.YOUTUBE_VIDEO,
          data_output=[report.data_output],
          topic_type=common_msg.TopicType.BRAND_OR_PRODUCT,
          topic=report.topic,
          start_time=report.start_time,
          end_time=report.end_time,
          status=wfe.Status.NEW,
          parent_execution_id=None,
          report_id=report.report_id,
          include_justifications=report.include_justifications,
      )
      video_execution_id = self._workflow_repo.create_execution(video_params)
      if common_msg.SocialMediaSource.YOUTUBE_VIDEO in report.sources:
        created_workflows[common_msg.SocialMediaSource.YOUTUBE_VIDEO.name] = (
            video_execution_id)

    if common_msg.SocialMediaSource.YOUTUBE_COMMENT in report.sources:
      if not video_execution_id:
        raise RuntimeError("Cannot create comment workflow without a parent.")
      comment_params = wfe.WorkflowExecutionParams(
          source=common_msg.SocialMediaSource.YOUTUBE_COMMENT,
          data_output=[report.data_output],
          topic_type=common_msg.TopicType.BRAND_OR_PRODUCT,
          topic=report.topic,
          start_time=report.start_time,
          end_time=report.end_time,
          status=wfe.Status.NEW,
          parent_execution_id=video_execution_id,
          report_id=report.report_id,
          include_justifications=report.include_justifications,
      )
      comment_execution_id = self._workflow_repo.create_execution(
          comment_params)
      created_workflows[common_msg.SocialMediaSource.YOUTUBE_COMMENT.name] = (
          comment_execution_id)

    return created_workflows


app = fastapi.FastAPI()
app_config = AppConfig()


@app.post(
    "/api/run_report",
    response_model=report_msg.SentimentReport,
    status_code=201,
)
def deaggregate_report(
    report: report_msg.SentimentReport) -> report_msg.SentimentReport:
  """Creates new workflow execution records from a SentimentReport message."""
  try:
    deaggregator_logic = Deaggregator(app_config.workflow_repo)

    # Generate a single, unique report_id for this entire request.
    report.report_id = str(uuid.uuid4())
    logger.info(
        "Generated new report_id '%s' for topic '%s'",
        report.report_id,
        report.topic,
    )

    created_workflows = deaggregator_logic.create_workflows(report=report)

    report.status = report_msg.Status.NEW
    report.created_on = datetime.datetime.now(datetime.timezone.utc)
    report.last_updated_on = report.created_on

    logger.info(
        "Created workflows for report_id %s: %s",
        report.report_id,
        created_workflows,
    )

    return report

  except (KeyError, ValueError) as e:
    raise fastapi.HTTPException(status_code=400, detail=f"Bad request: {e}")
  except Exception as e:
    logger.exception("An unexpected error occurred during de-aggregation.")
    raise fastapi.HTTPException(status_code=500,
                                detail="Internal Server Error") from e
