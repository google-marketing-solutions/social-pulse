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

  def setUp(self):
    super().setUp()
    self.mock_analyzer = mock.Mock(spec=apis.LlmApiClient)
    self.category_json_data = '[{"categoryName": "Test Category"}]'

    # Register mock analyzer
    service.registry.register(apis.LlmApiClient, self.mock_analyzer)

    self.categorizer = process_justifications.JustificationCategorizer(
        category_json_data=self.category_json_data,
        task_family="TestCategorizer"
    )

  def test_categorize_raises_error_if_no_justifications(self):
    """Raises ValueError if no justifications to categorize.

    Given a DataFrame with empty sentiments/justifications
    When categorize is called
    Then a ValueError is raised
    """
    df = pd.DataFrame([{
        "sentiments": []
    }])

    with self.assertRaisesRegex(ValueError, "No justifications to categorize"):
      self.categorizer.categorize(df)

  def test_categorize_calls_analyzer_and_updates_dataframe(self):
    """Calls analyzer and updates DataFrame with categories.

    Given a DataFrame with valid justifications
    And the analyzer returns valid categorization JSON
    When categorize is called
    Then the analyzer is called with the prompt
    And the DataFrame is updated with the categories
    """
    df = pd.DataFrame([{
        "sentiments": [{
            "justifications": [{"quote": "great feature"}]
        }]
    }])

    # Mock LLM response
    mock_response = json.dumps([{
        "id": "0_0_0",
        "category": "Feature: Quality"
    }])
    self.mock_analyzer.analyze_content_with_gemini.return_value = mock_response

    self.categorizer.categorize(df)

    self.mock_analyzer.analyze_content_with_gemini.assert_called_once()

    # Verify the category was added
    updated_sentiment = df.iloc[0]["sentiments"][0]
    self.assertEqual(
        updated_sentiment["justifications"][0]["category"],
        "Feature: Quality"
    )

  def test_categorize_handles_markdown_response(self):
    """Handles markdown-formatted JSON response from LLM.

    Given the analyzer returns markdown-wrapped JSON
    When categorize is called
    Then the response is correctly parsed and DataFrame updated
    """
    df = pd.DataFrame([{
        "sentiments": [{
            "justifications": [{"quote": "bad output"}]
        }]
    }])

    mock_response = "```json\n" + json.dumps([{
        "id": "0_0_0",
        "category": "General: Negative"
    }]) + "\n```"
    self.mock_analyzer.analyze_content_with_gemini.return_value = mock_response

    self.categorizer.categorize(df)

    updated_sentiment = df.iloc[0]["sentiments"][0]
    self.assertEqual(
        updated_sentiment["justifications"][0]["category"],
        "General: Negative"
    )

  def test_categorize_logs_error_on_failure(self):
    """Logs error and raises exception if categorization fails.

    Given the analyzer returns invalid JSON
    When categorize is called
    Then the JSONDecodeError is raised (and error logged implicitly)
    """
    df = pd.DataFrame([{
        "sentiments": [{
            "justifications": [{"quote": "error prone"}]
        }]
    }])

    self.mock_analyzer.analyze_content_with_gemini.return_value = "invalid json"

    with self.assertRaises(json.JSONDecodeError):
      self.categorizer.categorize(df)


class ProcessJustificationsTaskTest(
    unittest.TestCase,
    test_mixins.SetupMockSentimentTaskDepependenciesMixin
):

  def setUp(self):
    super().setUp()
    self.setup_all_mock_dependencies()

    # Mock the LlmApiClient registered in the service registry
    self.mock_analyzer = mock.Mock(spec=apis.LlmApiClient)
    service.registry.register(apis.LlmApiClient, self.mock_analyzer)

    self.task = process_justifications.ProcessJustificationsTask(
        execution_id="test_exec_id",
        my_required_task=self.mock_required_task
    )

  def test_run_validates_input_data(self):
    """Validates that input data has required columns.

    Given an input DataFrame missing the 'sentiments' column
    When run is called
    Then a ValueError is raised
    """
    # Mock input target to return invalid DF
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "other_col": []
    })
    # We need to mock input() to return our mock target
    with mock.patch.object(
        self.task,
        "input",
        return_value=self.mock_input_target
    ):
      with self.assertRaisesRegex(ValueError, "missing 'sentiments' column"):
        self.task.run()

  def test_run_successful_execution(self):
    """Successfully executes the categorization flow.

    Given valid input DataFrame with justifications
    And the analyzer returns valid prompts and categories
    When run is called
    Then input is validated
    And categories are generated
    And justifications are categorized and saved
    """
    # Setup input data
    input_df = pd.DataFrame([{
        "sentiments": [{
            "justifications": [{"quote": "awesome stuff"}],
            "sentimentScore": 0.9
        }],
        "summary": "Everything is awesome"
    }])
    self.mock_input_target.load_sentiment_data.return_value = input_df

    # Configure mock analyzer responses
    # First call: category generation
    # Second call: categorization
    self.mock_analyzer.analyze_content_with_gemini.side_effect = [
        '[{"categoryName": "General: Awesome"}]',
        json.dumps([{
            "id": "0_0_0",
            "category": "General: Awesome"
        }])
    ]

    # Mock output target
    mock_output_target = mock.Mock()
    with mock.patch.object(
        self.task,
        "input",
        return_value=self.mock_input_target
    ), \
    mock.patch.object(
        self.task,
        "output",
        return_value=mock_output_target
    ):
      self.task.run()

      # Validation
      self.mock_analyzer.analyze_content_with_gemini.assert_called()
      self.assertEqual(
          self.mock_analyzer.analyze_content_with_gemini.call_count, 2
      )

      # Verify output was written
      mock_output_target.write_sentiment_data.assert_called_once()
      args, _ = mock_output_target.write_sentiment_data.call_args
      output_df = args[0]

      self.assertEqual(
          output_df.iloc[0]["sentiments"][0]["justifications"][0]["category"],
          "General: Awesome"
      )

  def test_run_handles_batch_processing(self):
    """Handles processing of data in batches.

    Given input data with more rows than the batch size
    When run is called
    Then the categorizer is called multiple times
    """
    # Create DF with 2 rows, set batch size to 1
    input_df = pd.DataFrame([
        {
            "sentiments": [{"justifications": [{"quote": "q1"}]}],
            "summary": "s1"
        },
        {
            "sentiments": [{"justifications": [{"quote": "q2"}]}],
            "summary": "s2"
        }
    ])
    self.mock_input_target.load_sentiment_data.return_value = input_df

    # Mock responses
    self.mock_analyzer.analyze_content_with_gemini.side_effect = [
        '[{"categoryName": "C"}]',
        json.dumps([{"id": "0_0_0", "category": "C"}]),
        json.dumps([{"id": "1_0_0", "category": "C"}])
    ]

    mock_output_target = mock.Mock()

    # Patch MAX_JUSTIFICATIONS_PER_BATCH constant
    with mock.patch(
        "tasks.process_justifications.MAX_JUSTIFICATIONS_PER_BATCH", 1
    ), mock.patch.object(
        self.task, "input", return_value=self.mock_input_target
    ), mock.patch.object(
        self.task, "output", return_value=mock_output_target
    ):
      self.task.run()

      # 1 call for categories + 2 calls for batches = 3 calls
      self.assertEqual(
          self.mock_analyzer.analyze_content_with_gemini.call_count, 3
      )

      mock_output_target.write_sentiment_data.assert_called_once()
      args, _ = mock_output_target.write_sentiment_data.call_args
      self.assertEqual(len(args[0]), 2)  # Should still have 2 rows

  def test_run_generates_categories_if_empty(self):
    """Raises error if no justifications found to generate categories from.

    Given input DataFrame with empty justifications
    When run is called
    Then a ValueError is raised by _generate_category_description_json_data
    """
    input_df = pd.DataFrame([{
        "sentiments": [],
        "summary": "Nothing here"
    }])
    self.mock_input_target.load_sentiment_data.return_value = input_df

    with mock.patch.object(
        self.task, "input", return_value=self.mock_input_target
    ):
      with self.assertRaisesRegex(ValueError, "No justifications found"):
        self.task.run()
