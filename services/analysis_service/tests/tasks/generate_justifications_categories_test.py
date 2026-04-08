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

"""Tests for the generate_justifications_categories task."""

import unittest
from unittest import mock

import pandas as pd
import sentiment_task_mixins as test_mixins
from socialpulse_common import service
from tasks import generate_justifications_categories
from tasks.ports import apis


class GenerateJustificationCategoriesTaskTest(
    unittest.TestCase, test_mixins.SetupMockSentimentTaskDepependenciesMixin
):

  def setUp(self):
    super().setUp()
    self.setup_all_mock_dependencies()

    # Mock the LlmApiClient registered in the service registry
    self.mock_analyzer = mock.Mock(spec=apis.LlmApiClient)
    service.registry.register(apis.LlmApiClient, self.mock_analyzer)

    self.task = (
        generate_justifications_categories.GenerateJustificationCategoriesTask(
            execution_id="test_exec_id",
            my_required_task=self.mock_required_task,
        )
    )

  def test_run_validates_input_data(self):
    """Validates that input data has required columns.

    Given an input DataFrame missing the 'sentiments' column
    When run is called
    Then a ValueError is raised
    """
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame(
        {"other_col": []}
    )
    with mock.patch.object(
        self.task, "input", return_value=self.mock_input_target
    ):
      with self.assertRaisesRegex(ValueError, "missing 'sentiments' column"):
        self.task.run()

  def test_run_generates_empty_categories(self):
    """Outputs empty categories if no justifications are found.

    Given input DataFrame with empty justifications
    When run is called
    Then it gracefully returns an empty categories JSON
    """
    input_df = pd.DataFrame([{"sentiments": [], "summary": "Nothing here"}])
    self.mock_input_target.load_sentiment_data.return_value = input_df

    mock_output_target = mock.Mock()
    with (
        mock.patch.object(
            self.task, "input", return_value=self.mock_input_target
        ),
        mock.patch.object(self.task, "output", return_value=mock_output_target),
    ):
      self.task.run()

      self.mock_analyzer.analyze_content.assert_not_called()
      mock_output_target.write_sentiment_data.assert_called_once()

      args, _ = mock_output_target.write_sentiment_data.call_args
      output_df = args[0]
      self.assertEqual(len(output_df), 1)
      self.assertEqual(output_df.iloc[0]["category_json_data"], "[]")

  def test_run_successful_execution(self):
    """Successfully executes the category generation flow.

    Given valid input DataFrame with justifications
    When run is called
    Then the LLM is prompted for categories and the output is saved
    """
    input_df = pd.DataFrame(
        [
            {
                "sentiments": [
                    {
                        "justifications": [{"quote": "awesome stuff"}],
                        "sentimentScore": 0.9,
                    }
                ],
                "summary": "Everything is awesome",
            }
        ]
    )
    self.mock_input_target.load_sentiment_data.return_value = input_df

    mock_response = '[{"categoryName": "General: Awesome"}]'
    self.mock_analyzer.analyze_content.return_value = mock_response

    mock_output_target = mock.Mock()
    with (
        mock.patch.object(
            self.task, "input", return_value=self.mock_input_target
        ),
        mock.patch.object(self.task, "output", return_value=mock_output_target),
    ):
      self.task.run()

      self.assertEqual(self.mock_analyzer.analyze_content.call_count, 2)
      mock_output_target.write_sentiment_data.assert_called_once()

      args, _ = mock_output_target.write_sentiment_data.call_args
      output_df = args[0]
      self.assertEqual(len(output_df), 1)
      self.assertEqual(output_df.iloc[0]["category_json_data"], mock_response)

