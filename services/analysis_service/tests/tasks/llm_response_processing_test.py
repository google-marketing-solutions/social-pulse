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
import json
import unittest
from unittest import mock

import pandas as pd
import sentiment_task_mixins as test_mixins
from tasks import llm_response_processing as lrp


EMPTY_ANALYSIS_RESPONSE = (
    pd.DataFrame([
        {
            "summary": "",
            "relevanceScore": 0.0,
            "sentiments": [
                {
                    "productOrBrand": "",
                    "sentimentScore": "",
                }
            ]
        }
    ])
)


class ProcessLlmSentimentResponsesTest(
    unittest.TestCase,
    test_mixins.SetupMockSentimentTaskDepependenciesMixin
):
  def setUp(self):
    super().setUp()
    self.setup_all_mock_dependencies()

  def generate_test_llm_response(
      self,
      llm_sentiment_response: dict[str, any]
  ) -> str:
    encoded_sentiment_response = json.dumps(llm_sentiment_response)
    outer_response = {
        "candidates": [
            {
                "avgLogprobs": (
                    -0.027945819828245375
                ),
                "content": {
                    "parts": [
                        {
                            "text": encoded_sentiment_response
                        }
                    ],
                    "role": "model"
                },
                "finishReason": "STOP"
            }
        ],
        "createTime": "2025-05-27T16:27:16.684777Z",
        "modelVersion": "gemini-2.0-flash-001@default",
        "responseId": "5Oc1aOnlKZiam9IPn42_-Ak",
        "usageMetadata": {
            "candidatesTokenCount": 36,
            "candidatesTokensDetails": [
                {
                    "modality": "TEXT",
                    "tokenCount": 36
                }
            ],
            "promptTokenCount": 514,
            "promptTokensDetails": [
                {
                    "modality": "TEXT",
                    "tokenCount": 514
                }
            ],
            "totalTokenCount": 550,
            "trafficType": "ON_DEMAND"
        }
    }
    return json.dumps(outer_response)

  def assert_output_dataframe_matches(self, expected_df: pd.DataFrame) -> None:
    write_sentiment_args = (
        self.mock_sentiment_data_repo.write_sentiment_data.call_args
    )
    actual_df = write_sentiment_args.args[1]
    pd.testing.assert_frame_equal(actual_df, expected_df)

  def test_fails_if_input_is_missing_response_column(self):
    """Fails if the input is missing the response column.

    Given an input dataset missing the response column.
    When the task is executed.
    Then a ValueError is raised.
    """
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame(
        {"some_column": ["some_value"]}
    )

    with self.assertRaises(ValueError):
      task = lrp.ProcessLlmSentimentResponses(
          execution_id="some_execution_id",
          my_required_task=self.mock_required_task
      )
      task.run()

  def test_returns_empty_analysis_if_response_has_invalid_json(self):
    """Returns an empty analysis if the LLM response has invalid JSON.

    Given the LLM response has invalid JSON.
    When the task is executed.
    Then a ValueError is raised.
    """
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame([
        {
            "response": "!@#$%^&*()_+"
        }
    ])

    task = lrp.ProcessLlmSentimentResponses(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    with self.assertRaises(ValueError):
      task.run()

  def test_returns_empty_analysis_if_no_candidates_in_llm_response(self):
    """Returns empty analysis if no candidates in LLM response.

    Given the LLM response didn't have any candidates.
    When the task is executed.
    Then an empty analysis is returned.
    """
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame([
        {
            "response": json.dumps({"some_value": "a_value"})
        }
    ])

    task = lrp.ProcessLlmSentimentResponses(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    self.assert_output_dataframe_matches(EMPTY_ANALYSIS_RESPONSE)

  def test_returns_empty_analysis_if_no_parts_in_llm_response(self):
    """Returns empty analysis if no parts in LLM response.

    Given the LLM response didn't have any parts within the candidates.
    When the task is executed.
    Then an empty analysis is returned.
    """
    incomplete_message = {
        "candidates": [
            {
                "avgLogprobs": (
                    -0.027945819828245375
                ),
                "content": {
                    "parts": [],
                    "role": "model"
                },
                "finishReason": "STOP"
            }
        ]
    }
    response_json_string = json.dumps(incomplete_message)
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame([
        {"response": response_json_string}
    ])

    task = lrp.ProcessLlmSentimentResponses(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    self.assert_output_dataframe_matches(EMPTY_ANALYSIS_RESPONSE)

  def test_extract_sentiment_fields_from_sentiment_response(self):
    """Extracts sentiment fields from the LLM response.

    Given the LLM response contains the expected sentiment fields.
    When the task is executed.
    Then the sentiment fields are extracted and included in the output
      DataFrame.
    """

    llm_sentiment_response = {
        "summary": "a summary",
        "relevanceScore": 0.5,
        "sentiments": [
            {
                "sentimentScore": 0.7
            }
        ]
    }
    response_json_string = self.generate_test_llm_response(
        llm_sentiment_response
    )
    print(response_json_string)
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame([
        {"response": response_json_string}
    ])

    task = lrp.ProcessLlmSentimentResponses(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    self.assert_output_dataframe_matches(
        pd.DataFrame([
            {
                "summary": "a summary",
                "relevanceScore": 0.5,
                "sentiments": [
                    {
                        "sentimentScore": 0.7
                    }
                ]
            }
        ])
    )

  def test_raises_error_if_threshold_exceeded(self):
    """Raises an error if the error threshold is exceeded.

    Given a dataset with a high percentage of invalid JSON responses.
    When the task is executed.
    Then a ValueError is raised.
    """
    # Given
    invalid_responses = [{"response": "!@#$%^&*()_+"}] * 2
    valid_response = {
        "summary": "a summary",
        "sentiments": [{"relevanceScore": 0.5, "sentimentScore": 0.7}],
    }
    valid_response_str = self.generate_test_llm_response(valid_response)
    valid_responses = [{"response": valid_response_str}] * 8

    all_responses = invalid_responses + valid_responses
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame(
        all_responses
    )

    task = lrp.ProcessLlmSentimentResponses(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )

    # When/Then
    with self.assertRaises(ValueError):
      task.run()

  @mock.patch.object(
      lrp.ProcessLlmSentimentResponses, "extract_response_columns"
  )
  def test_handles_unexpected_exception_in_run(self, mock_extract_response):
    """Handles unexpected exceptions in the run method.

    Given extract_response_columns raises a generic Exception for 1 row and the
      error threshold is not exceeded.
    When the task is executed.
    Then the task completes and returns a DataFrame with one empty analysis and
      the rest valid.

    Args:
      mock_extract_response: Mock object for extract_response_columns.
    """
    # Given
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame(
        [{"response": "some response"}] * 11
    )

    valid_response = {
        "summary": "a summary",
        "relevanceScore": 0.5,
        "sentiments": [
            {
                "sentimentScore": 0.7
            }
        ]
    }
    mock_extract_response.side_effect = [
        Exception("An unexpected error occurred")
    ] + [pd.Series(valid_response)] * 10

    task = lrp.ProcessLlmSentimentResponses(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )

    # When
    task.run()

    # Then
    expected_results = (
        [EMPTY_ANALYSIS_RESPONSE]
        + [pd.DataFrame([valid_response])] * 10
    )
    expected_df = pd.concat(expected_results, ignore_index=True)
    self.assert_output_dataframe_matches(expected_df)
    self.assertEqual(mock_extract_response.call_count, 11)
