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

import pandas as pd
from tasks.ports import persistence


class BigQuerySentimentDataRepo(persistence.SentimentDataRepo):
  """Class for reading/writing sentiment data to BigQuery staging tables."""

  def __init__(self):
    # Create and store a reference to a BQ client
    pass

  def exists(self, table_name: str) -> bool:
    """Checks if a sentiment data set BQ table exists.

    Args:
      table_name: The name of the BQ table to check for existence.

    Returns:
      True if the table exists, False otherwise.
    """
    raise NotImplementedError

  def load_sentiment_data(self, table_name: str) -> pd.DataFrame:
    """Loads a sentiment data set from the specified BQ table.

    Loads the BQ dataset from configurations, then uses it to load all rows
    from a table within the configured data set.

    Args:
      table_name: The name of the table to load data from.

    Returns:
      A pandas DataFrame containing the sentiment data.
    """
    raise NotImplementedError

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
    raise NotImplementedError
