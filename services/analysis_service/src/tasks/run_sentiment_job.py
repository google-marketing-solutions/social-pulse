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
"""Task to execute the sentiment analysis job and wait for the results."""

import logging

from socialpulse_common import service
from tasks import core as tasks_core
from tasks.ports import apis


logger = logging.getLogger(__name__)


class RunSentimentAnalysisJobTask(tasks_core.SentimentTask):
  """Task to execute the sentiment analysis job.

  This task will create a job with the LLM to perform the analysis, using the
  preceding task's target data set as the input, and this tasks target as the
  output.

  Please note that this task will poll the job and only complete when the job
  has finished executing.
  """

  def run(self) -> None:
    """Executes the sentiment analysis job."""
    job_client: apis.LlmBatchJobApiClient = service.registry.get(
        apis.LlmBatchJobApiClient
    )

    job_client.submit_batch_job(
        input_table_name=self.my_required_task.output().table_name,
        output_table_name=self.output().table_name
    )
