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
#  limitations under the License.import unittest

import unittest
from unittest import mock

from infrastructure.apis import vertexai as vertexai_lib
from vertexai import batch_prediction


class VertexAiLlmBatchJobApiClientTest(unittest.TestCase):
  def setUp(self):
    super().setUp()

    self._setup_settings_config_mock()
    self._setup_vertexai_api_mocks()

    self.mock_time_sleep = self.enterContext(
        mock.patch("time.sleep", autospec=True)
    )

  def _setup_settings_config_mock(self):
    self.mock_settings = mock.MagicMock()

    self.enterContext(
        mock.patch(
            "socialpulse_common.config.Settings",
            return_value=self.mock_settings
        )
    )

  def _setup_vertexai_api_mocks(self):
    self.mock_vertexai_init = self.enterContext(
        mock.patch("vertexai.init", autospec=True)
    )

    self.mock_batch_prediction_job = mock.create_autospec(
        batch_prediction.BatchPredictionJob, instance=False
    )
    self.mock_batch_prediction_job.resource_name = "test-job"
    self.mock_batch_prediction_job.model_name = "test-model"
    self.mock_batch_prediction_job.state.name = "PENDING"
    self.mock_batch_prediction_job.has_ended = True
    self.mock_batch_prediction_job.has_succeeded = True

    self.mock_batch_prediction_job_class = self.enterContext(
        mock.patch.object(batch_prediction, "BatchPredictionJob", autospec=True)
    )
    self.mock_batch_prediction_job_class.submit.return_value = (
        self.mock_batch_prediction_job
    )

  def test_batch_job_is_submitted_with_correct_bq_uris(self):
    """Tests that the VertexAI job is submitted with the correct BigQuery URIs.

    Given an input and output table names
    When the batch job is submitted
    Then the VertexAI job is submitted with BQ URI paths for the tables.
    """
    input_table_name = "test_input_table"
    output_table_name = "test_output_table"

    client = vertexai_lib.VertexAiLlmBatchJobApiClient(
        "project_id",
        "region_id",
        "dataset_name"
    )
    client.submit_batch_job(input_table_name, output_table_name)

    self.mock_batch_prediction_job_class.submit.assert_called_once_with(
        source_model=mock.ANY,
        input_dataset="bq://project_id.dataset_name.test_input_table",
        output_uri_prefix="bq://project_id.dataset_name.test_output_table"
    )

  def test_submit_batch_job_waits_for_job_to_complete(self):
    """Tests that the submit_batch_job method waits for the job to complete.

    When the batch job is submitted
    Then API client waits for the job to complete.
    """
    self.mock_batch_prediction_job.has_ended = False
    num_calls_to_refresh_before_job_completes = 3

    # Setup mock to simulate the job ending after set calls to refresh
    refresh_call_count = 0
    def refresh_side_effect():
      nonlocal refresh_call_count
      refresh_call_count += 1
      if refresh_call_count >= num_calls_to_refresh_before_job_completes:
        setattr(self.mock_batch_prediction_job, "has_ended", True)
    self.mock_batch_prediction_job.refresh.side_effect = refresh_side_effect

    client = vertexai_lib.VertexAiLlmBatchJobApiClient(
        "project_id",
        "region_id",
        "dataset_name"
    )
    client.submit_batch_job("test_input_table", "test_output_table")

    self.assertEqual(
        self.mock_batch_prediction_job.refresh.call_count,
        num_calls_to_refresh_before_job_completes)

  def test_submit_batch_job_raises_error_if_job_fails(self):
    """Tests that the submit_batch_job method raises an error if the job fails.

    When the batch job is submitted
    And there is an error with the job
    Then API client raises an error.
    """
    self.mock_batch_prediction_job.resource_name = "failed_job"
    self.mock_batch_prediction_job.has_ended = True
    self.mock_batch_prediction_job.has_succeeded = False
    self.mock_batch_prediction_job.error = "test-error"

    client = vertexai_lib.VertexAiLlmBatchJobApiClient(
        "project_id",
        "region_id",
        "dataset_name"
    )
    with self.assertRaisesRegex(
        ValueError, "Job 'failed_job' failed: test-error"):
      client.submit_batch_job("input_table_name", "output_table_name")


if __name__ == "__main__":
  unittest.main()
