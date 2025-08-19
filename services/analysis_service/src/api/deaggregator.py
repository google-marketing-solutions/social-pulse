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
"""HTTP Cloud Function to de-aggregate a high-level analysis request.

This function acts as the primary API endpoint for Social Pulse.

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
from flask import jsonify
from flask import Request
import functions_framework


from infrastructure.persistence.postgresdb import client
from infrastructure.persistence.postgresdb import workflow_data_repo
from socialpulse_common import config
from socialpulse_common import service
from socialpulse_common.messages import workflow_execution as wfe
from tasks.ports import persistence


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

  logger.info("Starting service bootstrapping for deaggregator.")

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

  _is_initialized = True
  logger.info("Service bootstrapping complete.")


class DeaggregatorHandler:
  """Handles the logic of processing a single de-aggregation request."""

  def __init__(
      self,
      topic: str,
      start_date: datetime.date,
      end_date: datetime.date,
      sources: list[wfe.SocialMediaSource],
      outputs: list[wfe.SentimentDataType],
  ):
    self._topic = topic
    self._start_date = start_date
    self._end_date = end_date
    self._sources = sources
    self._outputs = outputs

  def process_request(self) -> dict[str, str]:
    """Creates and persists workflow execution records based on the request.

    Returns:
        A dictionary containing the IDs of the created workflows.

    Raises:
        RuntimeError: If the internal logic fails to produce a video execution
        ID before attempting to create a dependent comment workflow.
    """
    # Retrieve the persistence service via the abstract Port.
    workflow_repo = service_registry.get(
        persistence.WorkflowExecutionPersistenceService
    )
    created_workflows = {}
    video_execution_id = None

    # A video workflow is needed if either videos were explicitly requested
    # or comments were requested (as they depend on videos).
    needs_video_workflow = (
        wfe.SocialMediaSource.YOUTUBE_VIDEO in self._sources
        or wfe.SocialMediaSource.YOUTUBE_COMMENT in self._sources
    )

    if needs_video_workflow:
      video_params = wfe.WorkflowExecutionParams(
          source=wfe.SocialMediaSource.YOUTUBE_VIDEO,
          data_output=self._outputs,
          topic_type=wfe.TopicType.BRAND_OR_PRODUCT,
          topic=self._topic,
          start_time=self._start_date,
          end_time=self._end_date,
          status=wfe.Status.NEW,
          parent_execution_id=None,
      )
      video_execution_id = workflow_repo.create_execution(video_params)
      logger.info(
          "Created parent video workflow with ID: '%s'.", video_execution_id
      )

      if wfe.SocialMediaSource.YOUTUBE_VIDEO in self._sources:
        created_workflows[wfe.SocialMediaSource.YOUTUBE_VIDEO.name] = (
            video_execution_id
        )
      else:
        logger.info("This was an implicitly created parent workflow.")

    if wfe.SocialMediaSource.YOUTUBE_COMMENT in self._sources:
      if not video_execution_id:
        raise RuntimeError(
            "Cannot create comment workflow without a parent video workflow ID."
        )

      logger.info(
          "Creating YouTube comment workflow as a child of '%s'.",
          video_execution_id,
      )
      comment_params = wfe.WorkflowExecutionParams(
          source=wfe.SocialMediaSource.YOUTUBE_COMMENT,
          data_output=self._outputs,
          topic_type=wfe.TopicType.BRAND_OR_PRODUCT,
          topic=self._topic,
          start_time=self._start_date,
          end_time=self._end_date,
          status=wfe.Status.NEW,
          parent_execution_id=video_execution_id,
      )
      comment_execution_id = workflow_repo.create_execution(comment_params)
      logger.info(
          "Created child comment workflow with ID: '%s'.", comment_execution_id
      )
      created_workflows[wfe.SocialMediaSource.YOUTUBE_COMMENT.name] = (
          comment_execution_id
      )

    return created_workflows


@functions_framework.http
def deaggregator(request: Request):
  """HTTP-triggered cloud function that acts as the main entry point."""
  try:
    _bootstrap_services()
  except Exception:  # pylint: disable=broad-exception-caught
    logger.exception("Critical error during service bootstrapping.")
    return (
        jsonify({"error": "Internal Server Error during initialization"}),
        500,
    )

  # Basic web validation to ensure only POST requests are allowed.
  if request.method != "POST":
    return jsonify({"error": "Method not allowed"}), 405

  # Parse and hand off to Handler
  try:
    data = request.get_json(force=True)
    if not all(
        k in data
        for k in ["topic", "start_date", "end_date", "sources", "output"]
    ):
      raise ValueError("Missing required fields in request payload.")

    # Instantiate the handler with validated data
    handler = DeaggregatorHandler(
        topic=data["topic"],
        start_date=datetime.datetime.fromisoformat(data["start_date"]).date(),
        end_date=datetime.datetime.fromisoformat(data["end_date"]).date(),
        sources=[wfe.SocialMediaSource[s.upper()] for s in data["sources"]],
        outputs=[wfe.SentimentDataType[o.upper()] for o in data["output"]],
    )

    # Call the main processing method on the handler instance.
    created_workflows = handler.process_request()

    return (
        jsonify(
            {
                "message": "Workflows successfully created.",
                "created_workflows": created_workflows,
            }
        ),
        201,
    )

  except (ValueError, KeyError, TypeError) as e:
    logger.error("Invalid request payload: %s", e)
    return jsonify({"error": f"Bad Request: {e}"}), 400
  except Exception:  # pylint: disable=broad-exception-caught
    logger.exception("An unexpected error occurred during request processing.")
    return jsonify({"error": f"Internal Server Error: {e}"}), 500
