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
"""Generic BigQuery Client."""

import logging
from typing import Any, Dict, List, Optional

from google.cloud import bigquery


class BigQueryClient:
  """Client for interacting with BigQuery."""

  def __init__(self, project_id: Optional[str] = None):
    """Initializes the BigQuery client.

    Args:
       project_id: The GCP project ID. If None, inferred from environment.
    """
    self._client = bigquery.Client(project=project_id)
    self._logger = logging.getLogger(__name__)

  def query(self, query: str, job_config=None) -> List[Dict[str, Any]]:
    """Executes a query and returns the results as a list of dictionaries.

    Args:
      query: The SQL query to execute.
      job_config: Optional job configuration.

    Returns:
      A list of dictionaries representing the rows.
    """
    try:
      query_job = self._client.query(query, job_config=job_config)
      results = query_job.result()  # Waits for job to complete.

      # Convert Row objects to dictionaries
      return [dict(row) for row in results]
    except Exception as e:
      self._logger.error(f"Error executing BigQuery query: {e}")
      raise
