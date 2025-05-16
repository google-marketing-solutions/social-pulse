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
"""Module providing concrete implementation for LlmBatchJobApiClient."""

import logging
import time

from socialpulse_common import config
from tasks.ports import apis
import vertexai
from vertexai import batch_prediction


logger = logging.getLogger(__name__)


GEMINI_PRO_MODEL_ID = "gemini-2.0-flash-001"


class VertexAiLlmBatchJobApiClient(apis.LlmBatchJobApiClient):
  """Concrete implementation that utilizes VertexAI and Gemini LLM."""

  def __init__(self):
    self._settings = config.Settings()

  def submit_batch_job(
      self, input_table_name: str, output_table_name: str
  ) -> None:
    """Submits a VertexAI batch prediction job.

    This method submits a batch prediction job to VertexAI using the provided
    input and output table names.  It creates URI strings for the table names,
    submits a job via the VertexAI API, and then waits for the job to complete.

    Args:
      input_table_name: The name of the BigQuery table containing the input
        data.
      output_table_name: The name of the BigQuery table where the prediction
        results will be written.

    Raises:
      ValueError: If the batch prediction job fails.
    """
    input_table_uri = f"bq://{input_table_name}"
    output_table_uri = f"bq://{output_table_name}"

    batch_job = self._generate_batch_job(input_table_uri, output_table_uri)

    logger.info("Job resource name: %s", batch_job.resource_name)
    logger.info("Model resource name: %s", batch_job.model_name)

    while not batch_job.has_ended:
      time.sleep(30)
      batch_job.refresh()

    if batch_job.has_succeeded:
      logger.info("Job '%s' succeeded!", batch_job.resource_name)
    else:
      raise ValueError(
          f"Job '{batch_job.resource_name}' failed: {batch_job.error}"
      )

  def _generate_batch_job(
      self, input_table_uri: str, output_table_uri: str
  ) -> batch_prediction.BatchPredictionJob:
    """Generates a VertexAI batch prediction job.

    This method generates a batch prediction job using the provided input and
    output table URIs. It initializes the VertexAI environment and submits the
    batch prediction job with the specified model and input/output locations.

    Args:
      input_table_uri: The URI of the BigQuery table containing the input data.
      output_table_uri: The URI of the BigQuery table where the prediction
        results will be written.

    Returns:
      A batch prediction job object.
    """
    project_id = self._settings.cloud.project_id
    location = self._settings.cloud.region

    vertexai.init(project=project_id, location=location)
    return batch_prediction.BatchPredictionJob.submit(
        source_model=GEMINI_PRO_MODEL_ID,
        input_dataset=input_table_uri,
        output_uri_prefix=output_table_uri
    )
