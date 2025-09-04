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
from typing import Any

from socialpulse_common.messages import workflow_execution as wfe
from socialpulse_common.persistence import postgresdb_client as client
from tasks.ports import persistence


logger = logging.getLogger(__name__)


# Column index constants
EXECUTION_ID_COL_INDEX = 0
SOURCE_COL_INDEX = 1
DATAOUTPUTS_COL_INDEX = 2
TOPICTYPE_COL_INDEX = 3
TOPIC_COL_INDEX = 4
STARTDATE_COL_INDEX = 5
ENDDATE_COL_INDEX = 6
STATUS_COL_INDEX = 7
LASTCOMPLETEDTASK_COL_INDEX = 8
PARENT_EXECUTION_ID_COL_INDEX = 9
REPORT_ID_COL_INDEX = 10


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
        "  parentExecutionId, "
        "  reportId"
        "FROM WorkflowExecutionParams "
        "WHERE executionId = %s",
        (execution_id,),
    )
    if not row:
      raise ValueError(f"No workflow execution found with ID: {execution_id}")

    logger.debug("Raw row data = %s", row)
    return self._map_row_to_wfe_params(row)

  def _parse_data_outputs(
      self, from_db: list[str]
  ) -> list[wfe.SentimentDataType]:
    data_outputs = []
    for data_output in from_db:
      data_outputs.append(wfe.SentimentDataType[data_output])
    return data_outputs

  def create_execution(
      self, execution_params: wfe.WorkflowExecutionParams
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
          parentExecutionId,
          reportId
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING executionId;
    """
    data_outputs_as_names = [
        output.name for output in execution_params.data_output
    ]
    parent_execution_id = (
        execution_params.parent_execution_id
        if execution_params.parent_execution_id
        else None
    )

    report_id = execution_params.report_id or None

    params = (
        execution_params.source.name,
        data_outputs_as_names,
        execution_params.topic_type.name,
        execution_params.topic,
        execution_params.start_time,
        execution_params.end_time,
        parent_execution_id,
        report_id,
    )

    new_id = self._postgres_client.insert_row(query, params)
    return new_id

  def mark_last_completed_task(self, execution_id: str, task_name: str) -> None:
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
            status = 'IN_PROGRESS',
            lastUpdatedOn = NOW()
        WHERE executionId = %s;
    """
    params = (task_name, execution_id)
    self._postgres_client.update_row(query, params)

  def update_status(self, execution_id: str, status: wfe.Status) -> None:
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
    params = (status.name, execution_id)
    self._postgres_client.update_row(query, params)

  def find_ready_executions(self) -> list[wfe.WorkflowExecutionParams]:
    """Finds ready workflows using a SQL query with a self-join.

    This includes workflows with a 'NEW' status that either have no parent
    or have a parent that is 'COMPLETED'.

    Returns:
      A list of WorkflowExecutionParams objects for ready workflows.
    """

    query = """
        SELECT
            wep.executionId, wep.source, wep.dataOutputs, wep.topicType,
            wep.topic, wep.dateRangeStart, wep.dateRangeEnd, wep.status,
            wep.lastCompletedTask, wep.parentExecutionId
        FROM
            WorkflowExecutionParams wep
        LEFT JOIN
            WorkflowExecutionParams parent_wep ON wep.parentExecutionId = parent_wep.executionId
        WHERE
            (wep.status = 'NEW' AND wep.parentExecutionId IS NULL)
            OR
            (wep.status = 'NEW' AND parent_wep.status = 'COMPLETED');
    """
    rows = self._postgres_client.retrieve_rows(query)
    return [self._map_row_to_wfe_params(row) for row in rows]

  def _map_row_to_wfe_params(
      self, row: tuple[Any, ...]
  ) -> wfe.WorkflowExecutionParams:
    """Maps a raw database row tuple to a WorkflowExecutionParams data object.

    Args:
      row: A tuple of database values, ordered by the column index constants.

    Returns:
      A populated WorkflowExecutionParams object.
    """
    wfe_params = wfe.WorkflowExecutionParams()
    wfe_params.execution_id = row[EXECUTION_ID_COL_INDEX]
    wfe_params.source = wfe.SocialMediaSource[row[SOURCE_COL_INDEX]]
    wfe_params.data_output = self._parse_data_outputs(
        row[DATAOUTPUTS_COL_INDEX]
    )
    wfe_params.topic_type = wfe.TopicType[row[TOPICTYPE_COL_INDEX]]
    wfe_params.topic = row[TOPIC_COL_INDEX]
    wfe_params.start_time = row[STARTDATE_COL_INDEX]
    wfe_params.end_time = row[ENDDATE_COL_INDEX]
    wfe_params.status = wfe.Status[row[STATUS_COL_INDEX]]
    wfe_params.last_completed_task_id = row[LASTCOMPLETEDTASK_COL_INDEX] or ""
    wfe_params.parent_execution_id = row[PARENT_EXECUTION_ID_COL_INDEX] or ""
    wfe_params.report_id = row[REPORT_ID_COL_INDEX] or ""
    return wfe_params
