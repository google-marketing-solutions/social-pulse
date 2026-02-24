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
"""Tests for the Workflow Data Repository."""

import datetime
import unittest
from unittest import mock

from infrastructure.persistence.postgresdb import workflow_data_repo
from socialpulse_common.persistence import postgresdb_client


class PostgresDbWorkflowExecutionPersistenceServiceTest(unittest.TestCase):

  def setUp(self):
    super().setUp()

    self.mock_postgres_client = mock.Mock(
        spec=postgresdb_client.PostgresDbClient
    )
    self.repo = (
        workflow_data_repo.PostgresDbWorkflowExecutionPersistenceService(
            self.mock_postgres_client
        )
    )

  def test_load_execution_preserves_false_include_justifications(self):
    # Setup
    execution_id = "exec-123"
    # Row order matching constants in workflow_data_repo.py
    # EXECUTION_ID_COL_INDEX = 0
    # SOURCE_COL_INDEX = 1
    # DATAOUTPUTS_COL_INDEX = 2
    # TOPICTYPE_COL_INDEX = 3
    # TOPIC_COL_INDEX = 4
    # STARTDATE_COL_INDEX = 5
    # ENDDATE_COL_INDEX = 6
    # STATUS_COL_INDEX = 7
    # LASTCOMPLETEDTASK_COL_INDEX = 8
    # PARENT_EXECUTION_ID_COL_INDEX = 9
    # REPORT_ID_COL_INDEX = 10
    # INCLUDE_JUSTIFICATIONS = 11

    mock_row = (
        execution_id,
        "YOUTUBE_VIDEO",  # Source
        ["SENTIMENT_SCORE"],  # Data Outputs
        "BRAND_OR_PRODUCT",  # Topic Type
        "python",  # Topic
        datetime.datetime.now(),  # Start Date
        datetime.datetime.now(),  # End Date
        "NEW",  # Status
        None,  # Last Completed Task
        None,  # Parent Execution ID
        "report-123",  # Report ID
        False  # Include Justifications (Explicitly False)
    )
    self.mock_postgres_client.retrieve_row.return_value = mock_row

    # Act
    wfe_params = self.repo.load_execution(execution_id)

    # Assert
    self.assertFalse(
        wfe_params.include_justifications,
        "include_justifications should be False when False in DB"
    )

  def test_load_execution_defaults_to_true_if_none(self):
    # Setup
    execution_id = "exec-123"
    mock_row = (
        execution_id,
        "YOUTUBE_VIDEO",
        ["SENTIMENT_SCORE"],
        "BRAND_OR_PRODUCT",
        "python",
        datetime.datetime.now(),
        datetime.datetime.now(),
        "NEW",
        None,
        None,
        "report-123",
        None  # Include Justifications (None)
    )
    self.mock_postgres_client.retrieve_row.return_value = mock_row

    # Act
    wfe_params = self.repo.load_execution(execution_id)

    # Assert
    self.assertTrue(
        wfe_params.include_justifications,
        "include_justifications should be True when None in DB"
    )

if __name__ == "__main__":
  unittest.main()
