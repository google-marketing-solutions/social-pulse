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

"""Tests for the process_justifications task."""

import json
import unittest
from unittest import mock

import pandas as pd
import sentiment_task_mixins as test_mixins
from socialpulse_common import service
from tasks import process_justifications
from tasks.ports import apis


class JustificationCategorizerTest(unittest.TestCase):
  """Unit tests for the JustificationCategorizer class."""

  def setUp(self):
    super().setUp()
    self.mock_analyzer = mock.Mock(spec=apis.LlmApiClient)
    self.category_json_data = '[{"categoryName": "Test Category"}]'

    # Register mock analyzer
    service.registry.register(apis.LlmApiClient, self.mock_analyzer)

    self.categorizer = process_justifications.JustificationCategorizer(
        category_json_data=self.category_json_data,
        task_family="TestCategorizer",
    )

  def test_categorize_skips_if_no_justifications(self):
    """Skips categorization if no justifications to categorize.

    Given a DataFrame with empty sentiments/justifications
    When categorize is called
    Then it successfully returns without raising or calling the LLM
    """
    df = pd.DataFrame([{"sentiments": []}])

    self.categorizer.categorize(df)
    self.mock_analyzer.analyze_content.assert_not_called()

  def test_categorize_calls_analyzer_and_updates_dataframe(self):
    """Calls analyzer and updates DataFrame with categories.

    Given a DataFrame with valid justifications
    And the analyzer returns valid categorization JSON
    When categorize is called
    Then the analyzer is called with the prompt
    And the DataFrame is updated with the categories
    """
    df = pd.DataFrame(
        [{"sentiments": [{"justifications": [{"quote": "great feature"}]}]}]
    )

    # Mock LLM response
    mock_response = json.dumps(
        [{"id": "0_0_0", "category": "Feature: Quality"}]
    )
    self.mock_analyzer.analyze_content.return_value = mock_response

    self.categorizer.categorize(df)

    self.mock_analyzer.analyze_content.assert_called_once_with(
        mock.ANY, response_mime_type="application/json"
    )

    # Verify the category was added
    updated_sentiment = df.iloc[0]["sentiments"][0]
    self.assertEqual(
        updated_sentiment["justifications"][0]["category"], "Feature: Quality"
    )

  def test_categorize_handles_markdown_response(self):
    """Handles markdown-formatted JSON response from LLM.

    Given the analyzer returns markdown-wrapped JSON
    When categorize is called
    Then the response is correctly parsed and DataFrame updated
    """
    df = pd.DataFrame(
        [{"sentiments": [{"justifications": [{"quote": "bad output"}]}]}]
    )

    mock_response = (
        "```json\n"
        + json.dumps([{"id": "0_0_0", "category": "General: Negative"}])
        + "\n```"
    )
    self.mock_analyzer.analyze_content.return_value = mock_response

    self.categorizer.categorize(df)

    updated_sentiment = df.iloc[0]["sentiments"][0]
    self.assertEqual(
        updated_sentiment["justifications"][0]["category"], "General: Negative"
    )

  def test_categorize_logs_error_on_failure(self):
    """Logs error and raises exception if categorization fails.

    Given the analyzer returns invalid JSON
    When categorize is called
    Then the JSONDecodeError is raised (and error logged implicitly)
    """
    df = pd.DataFrame(
        [{"sentiments": [{"justifications": [{"quote": "error prone"}]}]}]
    )

    self.mock_analyzer.analyze_content.return_value = "invalid json"

    with self.assertRaises(json.JSONDecodeError):
      self.categorizer.categorize(df)

  def test_categorize_handles_batching_of_justifications(self):
    """Handles processing of justifications in batches.

    Given a DataFrame with more justifications than the batch size
    When categorize is called
    Then the analyzer is called multiple times
    """
    df = pd.DataFrame(
        [
            {
                "sentiments": [
                    {
                        "justifications": [
                            {"quote": "q1"},
                            {"quote": "q2"},
                            {"quote": "q3"},
                        ]
                    }
                ]
            }
        ]
    )

    self.mock_analyzer.analyze_content.side_effect = [
        json.dumps(
            [
                {"id": "0_0_0", "category": "C1"},
                {"id": "0_0_1", "category": "C2"},
            ]
        ),
        json.dumps([{"id": "0_0_2", "category": "C3"}]),
    ]

    with mock.patch(
        "tasks.process_justifications.MAX_JUSTIFICATIONS_TO_CATEGORIZE", 2
    ):
      self.categorizer.categorize(df)

      self.assertEqual(self.mock_analyzer.analyze_content.call_count, 2)

      updated_justifications = df.iloc[0]["sentiments"][0]["justifications"]
      self.assertEqual(updated_justifications[0]["category"], "C1")
      self.assertEqual(updated_justifications[1]["category"], "C2")
      self.assertEqual(updated_justifications[2]["category"], "C3")

  def test_categorize_batch_retries_on_failure(self):
    """Retries analyze_content on failure.

    Given the analyzer fails on the first call but succeeds on the second
    When categorize is called
    Then the analyzer is called twice
    And the DataFrame is updated with the categories
    """
    df = pd.DataFrame(
        [{"sentiments": [{"justifications": [{"quote": "retry me"}]}]}]
    )

    mock_response = json.dumps(
        [{"id": "0_0_0", "category": "Feature: Quality"}]
    )
    self.mock_analyzer.analyze_content.side_effect = [
        Exception("API Error"),
        mock_response,
    ]

    with mock.patch("time.sleep") as mock_sleep:
      self.categorizer.categorize(df)

      self.assertEqual(self.mock_analyzer.analyze_content.call_count, 2)
      mock_sleep.assert_called_once_with(1)

      updated_sentiment = df.iloc[0]["sentiments"][0]
      self.assertEqual(
          updated_sentiment["justifications"][0]["category"], "Feature: Quality"
      )


class ProcessJustificationsTaskTest(
    unittest.TestCase, test_mixins.SetupMockSentimentTaskDepependenciesMixin
):
  """Unit tests for the ProcessJustificationsTask class."""

  def setUp(self):
    super().setUp()
    self.setup_all_mock_dependencies()

    # Mock the LlmApiClient registered in the service registry
    self.mock_analyzer = mock.Mock(spec=apis.LlmApiClient)
    service.registry.register(apis.LlmApiClient, self.mock_analyzer)

    self.task = process_justifications.ProcessJustificationsTask(
        execution_id="test_exec_id", my_required_task=self.mock_required_task
    )

    self.mock_categories_target = mock.Mock()
    self.mock_input_dict = {
        "sentiment_data": self.mock_input_target,
        "categories": self.mock_categories_target,
    }

  def test_run_validates_input_data(self):
    """Validates that input data has required columns.

    Given an input DataFrame missing the 'sentiments' column
    When run is called
    Then a ValueError is raised
    """
    # Mock input target to return invalid DF
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame(
        {"other_col": []}
    )
    # We need to mock input() to return our mock target
    with mock.patch.object(
        self.task, "input", return_value=self.mock_input_dict
    ):
      with self.assertRaisesRegex(ValueError, "missing 'sentiments' column"):
        self.task.run()

  def test_run_successful_execution(self):
    """Successfully executes the categorization flow.

    Given valid input DataFrame with justifications
    And the analyzer returns valid categories
    When run is called
    Then input is validated
    And justifications are categorized and saved
    """
    # Setup input data
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
                "relevanceScore": 100,
            }
        ]
    )
    self.mock_input_target.load_sentiment_data.return_value = input_df

    # Configure mock categories target
    categories_df = pd.DataFrame(
        [{"category_json_data": '[{"categoryName": "General: Awesome"}]'}]
    )
    self.mock_categories_target.load_sentiment_data.return_value = categories_df

    # Configure mock analyzer responses
    self.mock_analyzer.analyze_content.side_effect = [
        json.dumps([{"id": "0_0_0", "category": "General: Awesome"}])
    ]

    # Mock output target
    mock_output_target = mock.Mock()
    with (
        mock.patch.object(
            self.task, "input", return_value=self.mock_input_dict
        ),
        mock.patch.object(self.task, "output", return_value=mock_output_target),
    ):
      self.task.run()

      # Validation
      self.mock_analyzer.analyze_content.assert_called_once_with(
          mock.ANY, response_mime_type="application/json"
      )

      # Verify output was written
      mock_output_target.write_sentiment_data.assert_called_once()
      args, _ = mock_output_target.write_sentiment_data.call_args
      output_df = args[0]

      self.assertEqual(
          output_df.iloc[0]["sentiments"][0]["justifications"][0]["category"],
          "General: Awesome",
      )

  def test_run_handles_batch_processing(self):
    """Handles processing of data in batches.

    Given input data with more rows than the batch size
    When run is called
    Then the categorizer is called multiple times
    """
    # Create DF with 2 rows, set batch size to 1
    input_df = pd.DataFrame(
        [
            {
                "sentiments": [{"justifications": [{"quote": "q1"}]}],
                "summary": "s1",
                "relevanceScore": 100,
            },
            {
                "sentiments": [{"justifications": [{"quote": "q2"}]}],
                "summary": "s2",
                "relevanceScore": 100,
            },
        ]
    )
    self.mock_input_target.load_sentiment_data.return_value = input_df

    # Configure mock categories target
    categories_df = pd.DataFrame(
        [{"category_json_data": '[{"categoryName": "C"}]'}]
    )
    self.mock_categories_target.load_sentiment_data.return_value = categories_df

    # Mock responses
    self.mock_analyzer.analyze_content.side_effect = [
        json.dumps([{"id": "0_0_0", "category": "C"}]),
        json.dumps([{"id": "1_0_0", "category": "C"}]),
    ]

    mock_output_target = mock.Mock()

    # Patch MAX_ROWS_OF_CONTENT_TO_CATEGORIZE constant
    with (
        mock.patch(
            "tasks.process_justifications.MAX_ROWS_OF_CONTENT_TO_CATEGORIZE", 1
        ),
        mock.patch.object(
            self.task, "input", return_value=self.mock_input_dict
        ),
        mock.patch.object(self.task, "output", return_value=mock_output_target),
    ):
      self.task.run()

      # 2 calls for batches
      self.assertEqual(
          self.mock_analyzer.analyze_content.call_count, 2
      )

      mock_output_target.write_sentiment_data.assert_called_once()
      args, _ = mock_output_target.write_sentiment_data.call_args
      self.assertEqual(len(args[0]), 2)  # Should still have 2 rows

  def test_run_skips_categorization_if_categories_empty(self):
    """Skips categorization if the upstream task generated no categories.

    Given input data
    And the upstream categories target returns []
    When run is called
    Then the data is written unmodified and LLM is not called
    """
    input_df = pd.DataFrame([{"sentiments": [], "summary": "Nothing here"}])
    self.mock_input_target.load_sentiment_data.return_value = input_df

    categories_df = pd.DataFrame([{"category_json_data": "[]"}])
    self.mock_categories_target.load_sentiment_data.return_value = categories_df

    mock_output_target = mock.Mock()
    with (
        mock.patch.object(
            self.task, "input", return_value=self.mock_input_dict
        ),
        mock.patch.object(self.task, "output", return_value=mock_output_target),
    ):
      self.task.run()

      self.mock_analyzer.analyze_content.assert_not_called()
      mock_output_target.write_sentiment_data.assert_called_once()
      args, _ = mock_output_target.write_sentiment_data.call_args
      self.assertEqual(len(args[0]), 1)
