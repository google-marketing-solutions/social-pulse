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
"""Module for the deaggregator service HTTP endpoint using FastAPI.

Its primary responsibilities are:
1.  Parse and validate the incoming high-level analysis request.
2.  For each source specified, create a corresponding WorkflowExecutionParams
    record in the PostgreSQL database with a NEW status.
3.  Establish the dependency chain between workflows by setting the
    'parent_execution_id' for dependent workflows (e.g. a comment analysis
    is dependent on its parent video analysis).

"""

import datetime
import logging
import os
import uuid
import fastapi

from infrastructure.persistence.postgresdb import client
from infrastructure.persistence.postgresdb import workflow_data_repo
import pydantic
from socialpulse_common import config
from socialpulse_common.messages import workflow_execution as wfe
from tasks.ports import persistence
import uvicorn

log_format = (
    "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format=log_format)
logger = logging.getLogger(__name__)

settings = config.Settings()


class DeaggregatorRequest(pydantic.BaseModel):
  """Defines the expected JSON body for a deaggregation request."""

  topic: str
  start_date: datetime.date
  end_date: datetime.date
  sources: list[str]
  output: list[str]


class DeaggregatorResponse(pydantic.BaseModel):
  """Defines the JSON response for a successful deaggregation."""

  message: str
  created_workflows: dict[str, str]
  report_id: str


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
            postgres_client
        )
    )
    logger.info("AppConfig initialized successfully.")


class Deaggregator:
  """Handles the logic of processing a single de-aggregation request."""

  def __init__(
      self, workflow_repo: persistence.WorkflowExecutionPersistenceService
  ):
    self._workflow_repo = workflow_repo

  def create_workflows(
      self,
      topic: str,
      start_date: datetime.date,
      end_date: datetime.date,
      sources: list[wfe.SocialMediaSource],
      outputs: list[wfe.SentimentDataType],
      report_id: str,
  ) -> dict[str, str]:
    """Creates and persists workflow records, ensuring dependencies are met."""
    created_workflows = {}
    video_execution_id = None

    needs_video_workflow = (
        wfe.SocialMediaSource.YOUTUBE_VIDEO in sources
        or wfe.SocialMediaSource.YOUTUBE_COMMENT in sources
    )

    if needs_video_workflow:
      video_params = wfe.WorkflowExecutionParams(
          source=wfe.SocialMediaSource.YOUTUBE_VIDEO,
          data_output=outputs,
          topic_type=wfe.TopicType.BRAND_OR_PRODUCT,
          topic=topic,
          start_time=start_date,
          end_time=end_date,
          status=wfe.Status.NEW,
          parent_execution_id=None,
          report_id=report_id,
      )
      video_execution_id = self._workflow_repo.create_execution(video_params)
      if wfe.SocialMediaSource.YOUTUBE_VIDEO in sources:
        created_workflows[wfe.SocialMediaSource.YOUTUBE_VIDEO.name] = (
            video_execution_id
        )

    if wfe.SocialMediaSource.YOUTUBE_COMMENT in sources:
      if not video_execution_id:
        raise RuntimeError("Cannot create comment workflow without a parent.")
      comment_params = wfe.WorkflowExecutionParams(
          source=wfe.SocialMediaSource.YOUTUBE_COMMENT,
          data_output=outputs,
          topic_type=wfe.TopicType.BRAND_OR_PRODUCT,
          topic=topic,
          start_time=start_date,
          end_time=end_date,
          status=wfe.Status.NEW,
          parent_execution_id=video_execution_id,
          report_id=report_id,
      )
      comment_execution_id = self._workflow_repo.create_execution(
          comment_params
      )
      created_workflows[wfe.SocialMediaSource.YOUTUBE_COMMENT.name] = (
          comment_execution_id
      )

    return created_workflows


FastAPI = fastapi.FastAPI
app = FastAPI()
app_config = AppConfig()


@app.post(
    "/api/deaggregate", response_model=DeaggregatorResponse, status_code=201
)
def deaggregate_report(request: DeaggregatorRequest) -> DeaggregatorResponse:
  """Creates new workflow execution records based on a high-level request."""
  try:
    deaggregator_logic = Deaggregator(app_config.workflow_repo)

    # Generate a single, unique report_id for this entire request.
    report_id = str(uuid.uuid4())
    logger.info(
        "Generated new report_id '%s' for topic '%s'", report_id, request.topic
    )

    sources = [wfe.SocialMediaSource[s.upper()] for s in request.sources]
    outputs = [wfe.SentimentDataType[o.upper()] for o in request.output]

    created_workflows = deaggregator_logic.create_workflows(
        topic=request.topic,
        start_date=request.start_date,
        end_date=request.end_date,
        sources=sources,
        outputs=outputs,
        report_id=report_id,
    )

    return DeaggregatorResponse(
        message="Workflows successfully created.",
        created_workflows=created_workflows,
        report_id=report_id,
    )
  except (KeyError, ValueError) as e:
    raise fastapi.HTTPException(status_code=400, detail=f"Bad request: {e}")
  except Exception as e:
    logger.exception("An unexpected error occurred during de-aggregation.")
    raise fastapi.HTTPException(
        status_code=500, detail="Internal Server Error"
    ) from e


if __name__ == "__main__":
  uvicorn.run(
      "deaggregator:app",
      host="0.0.0.0",
      port=8080,
      reload=True,
  )
