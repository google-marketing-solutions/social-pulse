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
"""Module for sentiment data related service repos."""

import logging

from google.cloud import bigquery
from google.cloud import exceptions
import pandas as pd
from tasks.ports import persistence


logger = logging.getLogger(__name__)


class BigQuerySentimentDataRepo(persistence.SentimentDataRepo):
  """Class for reading/writing sentiment data to BigQuery staging tables."""

  def __init__(self, gcp_project_id: str, bq_dataset_name: str):
    """Initializes the BigQuerySentimentDataRepo with a BigQuery client.

    Args:
      gcp_project_id: The Google Cloud Project ID where the BigQuery dataset
        resides.
      bq_dataset_name: The name of the BigQuery dataset to interact with.
    """
    self._client = bigquery.Client(project=gcp_project_id)
    self._gcp_project_id = gcp_project_id
    self._bq_dataset_name = bq_dataset_name

    logger.info(
        "BigQuery based repo built successfully (project=%s, dataset=%s).",
        self._gcp_project_id, self._bq_dataset_name
    )

  def exists(self, table_name: str) -> bool:
    """Checks if a sentiment data set BQ table exists.

    Args:
      table_name: The name of the BQ table to check for existence.

    Returns:
      True if the table exists, False otherwise.
    """
    try:
      table_name_ref = self._generate_table_ref(table_name)
      logger.debug("Checking if table exists:  %s", table_name_ref)

      self._client.get_table(table_name_ref)
      return True
    except exceptions.NotFound:
      return False  # Excpected exception if the table doesn't exist

  def load_sentiment_data(self, table_name: str) -> pd.DataFrame:
    """Loads a sentiment data set from the specified BQ table.

    Loads the BQ dataset from configurations, then uses it to load all rows
    from a table within the configured data set.

    Args:
      table_name: The name of the table to load data from.

    Returns:
      A pandas DataFrame containing the sentiment data.
    """

    query = f"SELECT * FROM `{self._generate_table_ref(table_name)}`"
    logger.debug("Executing query: %s", query)

    query_job = self._client.query(query)
    return query_job.to_dataframe()

  def write_sentiment_data(
      self,
      table_name: str,
      sentiment_dataset: pd.DataFrame
  ) -> None:
    """Writes a  sentiment data set to the specified BQ table.

    Loads the BQ dataset from configurations, then uses it to materialize the
    provided DataFrame to a BigQuery table within the ocnfigured dataset.

    Args:
      table_name: The name of the table to write data to.
      sentiment_dataset: The pandas DataFrame containing the sentiment data to
        write.
    """
    load_data_job = self._client.load_table_from_dataframe(
        sentiment_dataset,
        self._generate_table_ref(table_name),
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"),
    )

    # Wait for the load job to complete
    load_data_job.result()

  def _generate_table_ref(self, table_name: str) -> str:
    """Generates a fully qualified table reference string.

    This method constructs a string that represents the full path to a table
    within BigQuery, including the project ID, dataset name, and table name.

    Args:
      table_name: The name of the table.

    Returns:
      A string representing the fully qualified table reference.
    """
    return f"{self._gcp_project_id}.{self._bq_dataset_name}.{table_name}"
