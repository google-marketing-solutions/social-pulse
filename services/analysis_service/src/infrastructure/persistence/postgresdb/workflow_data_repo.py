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
"""Module for loading workflow data params from the Social Post PostgresDB."""
import logging

from google.protobuf import timestamp_pb2
from socialpulse_common.messages import workflow_execution_pb2 as wfe
from tasks.ports import persistence

from . import client


logger = logging.getLogger(__name__)


class PostgresDbWorkflowExecutionPersistenceService(
    persistence.WorkflowExecutionPersistenceService
):
  """Class for loading and updating workflow data params from PostgresDB."""

  def __init__(self, postgres_client: client.PostgresDbClient):
    self._postgres_client = postgres_client

  def load_execution(self, execution_id: str) -> wfe.WorkflowExecutionParams:
    """Loads workflow execution parameters from Postgress DB via an SQL query.

    Args:
      execution_id: The ID of the workflow execution to load.

    Returns:
      A WorkflowExecutionParams object containing the loaded parameters.
    """
    row = self._postgres_client.retrieve_row(
        "SELECT "
        "  executionId, "
        "  source, "
        "  dataOutputs, "
        "  topicType, "
        "  topic, "
        "  dateRangeStart, "
        "  dateRangeEnd, "
        "  status, "
        "  lastCompletedTask, "
        "  parentExecutionId "
        "FROM WorkflowExecutionParams "
        "WHERE executionId = %s",
        (execution_id,),
    )
    if not row:
      raise ValueError(f"No workflow execution found with ID: {execution_id}")

    source_lookup = wfe.SocialMediaSource.DESCRIPTOR.values_by_name
    topic_type_lookup = wfe.TopicType.DESCRIPTOR.values_by_name
    status_lookup = wfe.Status.DESCRIPTOR.values_by_name
    logger.debug("Raw row data = %s", row)
    wfe_params = wfe.WorkflowExecutionParams()
    wfe_params.execution_id = row[0]
    wfe_params.source = source_lookup[row[1]].number
    wfe_params.data_output.extend(self._parse_data_outputs(row[2]))
    wfe_params.topic_type = topic_type_lookup[row[3]].number
    wfe_params.topic = row[4]

    start_time_proto = timestamp_pb2.Timestamp()
    start_time_proto.FromDatetime(row[5])
    wfe_params.start_time.CopyFrom(start_time_proto)

    end_time_proto = timestamp_pb2.Timestamp()
    end_time_proto.FromDatetime(row[6])
    wfe_params.end_time.CopyFrom(end_time_proto)

    wfe_params.status = status_lookup[row[7]].number
    wfe_params.last_completed_task_id = row[8] if row[8] else ""

    wfe_params.parent_execution_id = row[9] if row[9] else ""

    return wfe_params

  def _parse_data_outputs(
      self,
      from_db: list[str]
  ) -> list[wfe.SentimentDataType]:
    data_outputs = []
    sentiment_data_type_lookup = wfe.SentimentDataType.DESCRIPTOR.values_by_name

    for data_output in from_db:
      data_outputs.append(sentiment_data_type_lookup[data_output].number)
    return data_outputs

  def create_execution(
      self,
      execution_params: wfe.WorkflowExecutionParams
  ) -> str:
    """Saves workflow execution parameters to PostgresDB via an SQL INSERT.

    Args:
      execution_params: The workflow execution parameters.

    Returns:
      str: The ID of the newly created workflow execution.

    """
    query: str = """
        INSERT INTO WorkflowExecutionParams (
          source,
          dataOutputs,
          topicType,
          topic,
          dateRangeStart,
          dateRangeEnd,
          parentExecutionId
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING executionId;
    """
    data_outputs_as_names = [
        wfe.SentimentDataType.Name(output)
        for output in execution_params.data_output
    ]
    parent_exeuction_id = (
        execution_params.parent_execution_id
        if execution_params.parent_execution_id else None
    )

    params = (
        wfe.SocialMediaSource.Name(execution_params.source),
        data_outputs_as_names,
        wfe.TopicType.Name(execution_params.topic_type),
        execution_params.topic,
        execution_params.start_time.ToDatetime(),
        execution_params.end_time.ToDatetime(),
        parent_exeuction_id
    )

    new_id = self._postgres_client.insert_row(query, params)
    return new_id

  def mark_last_completed_task(
      self,
      execution_id: str,
      task_name: str
  ) -> None:
    """Marks the last completed task for a workflow execution.

    Args:
      execution_id: The ID of the workflow execution.
      task_name: The name of the task that was just completed.

    Raises:
      psycopg2.Error: If there is an error executing the query.
    """

    query: str = """
        UPDATE WorkflowExecutionParams
        SET lastCompletedTask = %s,
            status = 'STATUS_IN_PROGRESS',
            lastUpdatedOn = NOW()
        WHERE executionId = %s;
    """
    params = (task_name, execution_id)
    self._postgres_client.update_row(query, params)

  def update_status(
      self,
      execution_id: str,
      status: wfe.Status
  ) -> None:
    """Updates the status of a workflow execution.

    Args:
      execution_id: The ID of the workflow execution.
      status: The new status of the workflow execution.
    """
    query: str = """
        UPDATE WorkflowExecutionParams
        SET status = %s,
            lastUpdatedOn = NOW()
        WHERE executionId = %s;
    """
    params = (wfe.Status.Name(status), execution_id)
    self._postgres_client.update_row(query, params)
