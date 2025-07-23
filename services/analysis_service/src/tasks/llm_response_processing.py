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
"""Flatten LLM Response."""
import json
import logging
import pandas as pd

from tasks import core as tasks_core


logger = logging.getLogger(__name__)


# Response column name
RESPONSE_COLUMN_NAME = "response"


# Sentiment analysis columns extracted from the LLM response
SUMMARY_COL_NAME = "summary"
SENTIMENTS_COL_NAME = "sentiments"
RELEVANCE_SCORE_COL_NAME = "relevanceScore"
SENTIMENT_SCORE_COL_NAME = "sentimentScore"


# An empty sentiment analysis response, in case the LLM failed to provide one
EMPTY_SENTIMENT_RESPONSE = {
    SUMMARY_COL_NAME: "",
    SENTIMENTS_COL_NAME: [
        {
            RELEVANCE_SCORE_COL_NAME: 0.0,
            SENTIMENT_SCORE_COL_NAME: 0.0,
        }
    ],
}


class ProcessLlmSentimentResponses(tasks_core.SentimentTask):
  """Luigi Task to process and flatten LLM responses for sentiment analysis.

  This task reads the raw JSON output from a batch prediction job, parses the
  nested JSON, flattens the array of sentiment results, and joints it back
  with the raw results data.
  """

  def _validate_input_dataset(self, dataset: pd.DataFrame):
    """Validates the input data set for completeness.

    This method checks if the input dataset contains the required columns:
    1) LLM responses.

    Args:
      dataset: The pandas DataFrame
    Raises:
      ValueError: If a required column was missing.
    """
    if RESPONSE_COLUMN_NAME not in dataset.columns:
      raise ValueError(
          f"[{self.task_family}] LLM results DataFrame missing "
          f"'{RESPONSE_COLUMN_NAME}' column."
      )

  def extract_response_columns(self, row: pd.Series) -> pd.Series:
    """Extracts sentiment-related columns from the raw LLM response string.

    Args:
      row: A pandas Series representing a row from the DataFrame containing the
        raw LLM response string in the column specified by RESPONSE_COLUMN_NAME.

    Returns:
      A pandas Series containing the extracted 'summary', 'relevanceScore', and
      'sentimentScore' values, or an empty response if values couldn't be
      extracted.
    """
    try:
      prediction_json_str = row[RESPONSE_COLUMN_NAME]
      llm_response = json.loads(prediction_json_str)

      if "candidates" not in llm_response:
        logger.info("[%s] No candidates in LLM response.", self.task_family)
        return pd.Series(EMPTY_SENTIMENT_RESPONSE)

      candidate = llm_response["candidates"][0]
      content = candidate["content"]

      # Response comes with unnecessary list of 'parts' we need to deal with
      parts = content["parts"]
      if "parts" not in content or not content["parts"]:
        logger.info("[%s] No parts in LLM response.", self.task_family)
        return pd.Series(EMPTY_SENTIMENT_RESPONSE)
      text = parts[0]["text"]
      analysis = json.loads(text)

      return pd.Series({
          SUMMARY_COL_NAME: analysis.get(SUMMARY_COL_NAME, ""),
          SENTIMENTS_COL_NAME: analysis.get(SENTIMENTS_COL_NAME, []),
      })
    except Exception as e:  # pylint: disable=broad-exception-caught
      logger.exception(
          "[%s] Error navigating LLM prediction JSON structure: %s. "
          "Snippet: %s",
          self.task_family,
          e,
          prediction_json_str[:250] if prediction_json_str else ""
      )
      raise

  def run(self) -> None:
    """Loads LLM results, parses JSON, flattens, and saves."""
    logger.info(
        "[%s] Starting task for execution ID: %s",
        self.task_family,
        self.execution_id,
    )

    llm_results = self.input().load_sentiment_data()
    logger.debug(
        "[%s] Reading LLM results from sentiment data set: %s",
        self.task_family,
        self.input().table_name
    )

    self._validate_input_dataset(llm_results)
    llm_results[["summary", "sentiments"]] = (
        llm_results.apply(self.extract_response_columns, axis=1)
    )
    llm_results = llm_results.drop(columns=[RESPONSE_COLUMN_NAME])

    self.output().write_sentiment_data(llm_results)
