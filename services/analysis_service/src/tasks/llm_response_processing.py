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
from typing import Any, List, Dict
import pandas as pd

from socialpulse_common import config
from socialpulse_common import service
from tasks import core as tasks_core
from tasks import run_sentiment_job
from tasks.ports import persistence


settings = config.Settings()


def _parse_and_flatten_llm_json_response(
    prediction_json_str: str | None, task_family: str
) -> List[Dict[str, Any]]:
  """Parses the LLM's full JSON response string.

  extracts the actual sentiment analysis JSON,
  and then flattens that.

  Args:
    prediction_json_str: json response to parse
    task_family: Luigi task for logging

  Returns:
    A list of dictionaries, where each dictionary contains the parsed
    sentiment analysis for a single product/brand. Returns an empty
    list if parsing fails, the input is empty, or no valid sentiment
    analyses are found.
  """
  flattened_results = []
  if not prediction_json_str:
    logging.warning("[%s] Received empty prediction JSON string.", task_family)
    return flattened_results

  try:
    # Parse the outer LLM JSON response
    vertex_ai_output = json.loads(prediction_json_str)

    # Get the actual LLM text output
    if not vertex_ai_output.get("candidates"):
      logging.warning(
          "[%s] 'candidates' field missing in LLM response.", task_family
      )
      return flattened_results
    if (
        not isinstance(vertex_ai_output["candidates"], list)
        or not vertex_ai_output["candidates"]
    ):
      return flattened_results

    candidate = vertex_ai_output["candidates"][0]
    if not candidate.get("content") or not candidate["content"].get("parts"):
      logging.warning(
          "[%s] 'content' or 'parts' missing in candidate.", task_family
      )
      return flattened_results
    if (
        not isinstance(candidate["content"]["parts"], list)
        or not candidate["content"]["parts"]
    ):
      logging.warning("[%s] 'parts' is not a non-empty list.", task_family)
      return flattened_results

    llm_sentiment_json_str = candidate["content"]["parts"][0].get("text")
    if not llm_sentiment_json_str:
      logging.warning(
          "[%s] 'text' field containing sentiment JSON is missing or empty.",
          task_family,
      )
      return flattened_results

    # Parse the inner sentiment JSON string
    sentiment_analyses = json.loads(llm_sentiment_json_str)
    if not isinstance(sentiment_analyses, list):
      logging.warning(
          "[%s] Parsed sentiment analysis is not a list as expected: %s",
          task_family,
          type(sentiment_analyses),
      )
      return flattened_results

    for analysis_item in sentiment_analyses:
      if isinstance(analysis_item, dict):
        flattened_results.append(analysis_item)
      else:
        logging.warning(
            "[%s] Item in sentiment analysis list is not a dict: %s",
            task_family,
            analysis_item,
        )
    return flattened_results

  except json.JSONDecodeError as e:
    logging.error(
        "[%s] Failed to decode JSON from LLM prediction: %s. Snippet: %s",
        task_family,
        e,
        prediction_json_str[:200],
    )
    return []
  except (KeyError, IndexError, TypeError) as e:
    logging.error(
        "[%s] Error navigating LLM prediction JSON structure: %s. Snippet: %s",
        task_family,
        e,
        prediction_json_str[:200],
    )
    return []
  except Exception as e:  # pylint: disable=broad-exception-caught
    logging.exception(
        "[%s] Unexpected error parsing LLM prediction: %s", task_family, e
    )
    return []


class ProcessLlmVideoResponses(tasks_core.SentimentTask):
  """Luigi Task to process and flatten LLM responses for video analysis.

  This task reads the raw JSON output from a Vertex AI Batch Prediction job
  (which was run by a RunSentimentAnalysisJobTask), parses the nested JSON,
  flattens the array of sentiment results, joins with original videoId,
  and saves the structured, flattened data.
  """

  def requires(self) -> run_sentiment_job.RunSentimentAnalysisJobTask:
    """This task requires RunSentimentAnalysisJobTask to complete.

    Returns:
      The required ProcessLlmVideoResponses task instance.
    """
    required_task = super().requires()
    if not isinstance(
        required_task, run_sentiment_job.RunSentimentAnalysisJobTask
    ):
      raise TypeError(
          f"[{self.task_family}] requires RunSentimentAnalysisJobTask, but got "
          f"{type(required_task).__name__}"
      )
    return required_task

  def output(self) -> tasks_core.SentimentDataRepoTarget:
    """Defines the output target for this task.

    Output is a BigQuery table containing the final flattened sentiment data.

    Returns:
      An instance of SentimentDataRepoTarget representing the task's
      output dataset.
    """
    return tasks_core.SentimentDataRepoTarget(self.dataset_name)

  def run(self) -> None:
    """Loads LLM results, parses JSON, flattens, and saves."""
    logging.info(
        "[%s] Starting task for execution ID: %s",
        self.task_family,
        self.execution_id,
    )

    try:
      # Get the BigQuery table name where LLM results are stored.
      # output of the required RunSentimentAnalysisJobTask.
      llm_results_target = self.input()
      results_bq_table_name = llm_results_target.table_name
      logging.info(
          "[%s] Reading LLM results from BQ table: %s",
          self.task_family,
          results_bq_table_name,
      )

      # Load Raw LLM Results from BigQuery
      data_repo: persistence.SentimentDataRepo = service.registry.get(
          persistence.SentimentDataRepo
      )
      # The upstream task RunSentimentAnalysisJobTask ensures this table exists.
      raw_results_df = data_repo.load_sentiment_data(results_bq_table_name)
      logging.info(
          "[%s] Loaded %d rows from LLM results table %s",
          self.task_family,
          len(raw_results_df),
          results_bq_table_name,
      )

      # Define expected columns for the final flattened DataFrame
      final_flattened_columns = [
          "videoId",
          "productOrBrand",
          "sentimentScore",
          "relevanceScore",
          "summary",
      ]

      if raw_results_df.empty:
        logging.warning(
            "[%s] LLM results table %s is empty. Writing empty output.",
            self.task_family,
            results_bq_table_name,
        )
        self.output().write_sentiment_data(
            pd.DataFrame(columns=final_flattened_columns)
        )
        return

      # Parse and Flatten LLM JSON Responses
      results_column_name = "response"
      if results_column_name not in raw_results_df.columns:
        raise ValueError(
            f"[{self.task_family}] LLM results DataFrame missing "
            f"'{results_column_name}' column."
        )

      all_flattened_sentiments = []
      # Iterate through each row (each original video sent to LLM)
      for _, row_from_bq in raw_results_df.iterrows():
        llm_prediction_json_str = row_from_bq[results_column_name]

        # Parse the LLM's output
        parsed_sentiment_list = _parse_and_flatten_llm_json_response(
            llm_prediction_json_str, self.task_family
        )

        # each individual sentiment analysis result from the LLM for this video
        for sentiment_result_dict in parsed_sentiment_list:
          flat_record = {}
          flat_record["videoId"] = row_from_bq["videoId"]

          # Add fields from the parsed LLM sentiment_result_dict
          flat_record.update(sentiment_result_dict)
          all_flattened_sentiments.append(flat_record)

      final_df = pd.DataFrame(all_flattened_sentiments)
      logging.info(
          "[%s] Processed LLM responses into %d flattened sentiment records.",
          self.task_family,
          len(final_df),
      )

      # Select/Reorder Columns and Ensure Types
      if not final_df.empty:
        # Ensure all desired columns exist, add NaNs if not
        for col in final_flattened_columns:
          if col not in final_df.columns:
            final_df[col] = pd.NA

        final_df = final_df[final_flattened_columns]
        # type conversions:
        if "sentimentScore" in final_df.columns:
          final_df["sentimentScore"] = pd.to_numeric(
              final_df["sentimentScore"], errors="coerce"
          )
        if "relevanceScore" in final_df.columns:
          final_df["relevanceScore"] = pd.to_numeric(
              final_df["relevanceScore"], errors="coerce"
          )

      # Save Final Flattened Dataset
      self.output().write_sentiment_data(final_df)
      logging.info(
          "[%s] Successfully wrote flattened sentiment data to %s",
          self.task_family,
          self.output().table_name,
      )

    except Exception as e:
      logging.exception(
          "[%s] Task failed during execution %s due to %s: %s",
          self.task_family,
          self.execution_id,
          type(e).__name__,
          e,
      )
      raise
