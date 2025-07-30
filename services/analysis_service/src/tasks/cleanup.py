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
"""Task for cleanup after a sentiment run (ie, removed staging datasets)."""

from socialpulse_common import service
from tasks import constants
from tasks import core as tasks_core
from tasks.ports import persistence


class CleanupTask(tasks_core.SentimentTask):
  """Luigi Task for performing cleanup operations after a workfkow execution.

  This task is responsible for copying the final sentiment analysis results
  from the last task's output table to a permanent, uniquely named dataset
  within the SentimentDataRepo. The naming convention for the final dataset
  includes the workflow execution ID, source, and output type.
  """

  @property
  def dataset_name(self) -> str:
    """Generates the name for the final sentiment data table.

    The name is constructed using a prefix, the social media source,
    the sentiment data type, and the workflow execution ID.

    Returns:
      A string representing the final sentiment data table name.
    """
    return self._generate_sentiment_data_table_name()

  def run(self):
    """Executes the cleanup task."""
    last_task_output_table = self.my_required_task.output().table_name
    sentiment_data_repo = service.registry.get(
        persistence.SentimentDataRepo
    )

    sentiment_data_repo.copy_sentiment_data(
        last_task_output_table,
        self._generate_sentiment_data_table_name()
    )

  def _generate_sentiment_data_table_name(self):
    """Generates the name for the final sentiment data table.

    Returns:
      A string representing the final sentiment data table name.
    """
    execution_id = self.execution_id
    return (
        f"{constants.SENTIMENT_RESULTS_DATASET_PREFIX}_{execution_id}"
    )
