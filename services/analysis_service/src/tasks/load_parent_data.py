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
"""Task for loading the data from the parent workflow execution."""

from socialpulse_common import service
from tasks import constants
from tasks import core as tasks_core
from tasks.ports import persistence


class LoadParentWorkflowDatasetTask(tasks_core.SentimentTask):
  """Luigi Task to load data from a parent workflow execution.

  This task is responsible for copying the final sentiment analysis results
  from a specified parent workflow execution's permanent dataset into the
  current workflow's staging dataset. This allows subsequent tasks in the
  current workflow to operate on the data from the parent.
  """

  def _generate_parent_sentiment_dataset_name(self):
    """Generates the name for the parent sentiment data table.

    Returns:
      A string representing the parent sentiment data table name.
    """
    return (
        f"{constants.SENTIMENT_RESULTS_DATASET_PREFIX}_"
        f"{self.workflow_exec.parent_execution_id}"
    )

  def run(self):
    """Executes the cleanup task."""
    source_dataset_name = self._generate_parent_sentiment_dataset_name()
    sentiment_data_repo = service.registry.get(
        persistence.SentimentDataRepo
    )
    sentiment_data_repo.copy_sentiment_data(
        source_dataset_name,
        self.dataset_name
    )
