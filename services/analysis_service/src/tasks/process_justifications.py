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

import json
import logging
import string

import luigi
import pandas as pd
from socialpulse_common import service
from socialpulse_common.utils import markdown
from tasks import constants
from tasks import core as tasks_core
from tasks.generate_justifications_categories import GenerateJustificationCategoriesTask
from tasks.ports import apis


logger = logging.getLogger(__name__)

# Controls the maximum number of justifications to send to the LLM in a single
# batch. This is done to avoid overwhelming the LLM with too large of a request
# by limiting the number of justifications it needs to process per prompt.
MAX_JUSTIFICATIONS_PER_BATCH = 50

BULK_CATEGORIZATION_PROMPT_TEMPLATE = """
  You are an expert sentiment analyst. Your goal is to categorize a list of
  customer feedback justifications into specific, pre-defined categories.

  # Input Data
  1. **Categories**: A list of defined categories with names, definitions, and
     types.
     ${category_json_data}
  2. **Justifications**: A list of feedback quotes to be categorized.
     ${justifications_json_data}

  # Methodology: Chain of Thought
  For each justification in the list, you must internally:
  1. **Analyze the Quote**: Read the quote and identify the core subject (e.g.,
     a specific feature, general reliability, pricing).
  2. **Match with Categories**: Compare the core subject against the provided
     "Categories". Look for:
     - Exact feature matches (e.g., "Firefly" -> "Feature: AI Tools").
     - Sentiment thematic matches (e.g., "Love the workflow" -> "General: Ease
       of Use").
     - Use the 'definition' and 'representativeExample' fields in the Categories
       to guide your choice.
  3. **Select Best Fit**: Choose the single most accurate category name.
     - If the quote is vague or doesn't fit ANY category, use "[Uncategorized]".
     - If it fits multiple, prioritize "Feature Specific" over "General
       Sentiment" if the quote explicitly names a feature.

  # Constraints
  - Return ONLY a valid JSON list of objects.
  - Do not include markdown formatting code blocks in the output.
  - Ensure every input ID is returned in the output.

  # Output Format
  [
    {
      "id": "unique_id_from_input",
      "category": "Expert Selected Category Name"
    },
    ...
  ]
  """


class JustificationCategorizer:
  """Categorizes justifications using an LLM."""

  def __init__(
      self,
      category_json_data: str,
      task_family: str = "JustificationCategorizer",
  ):
    """Initializes the JustificationCategorizer.

    Args:
      category_json_data: The category data, as a JSON string.
      task_family: The name of the task using this categorizer (for logging).
    """
    self._category_json_data = category_json_data
    self._task_family = task_family

  def categorize(self, df: pd.DataFrame) -> None:
    """Adds a category to the nested justifications in the sentiment data.

    This function will add a new column to the sentiment data, containing the
    category for each justification.

    Args:
      df: The sentiment data to add the category to.
    """
    flattened_justifications = self._flatten_and_tag_justifications(df)
    if not flattened_justifications:
      logging.info("[%s] No justifications to categorize.", self._task_family)
      return

    logging.debug(
        "[%s] Flattened %d justifications.",
        self._task_family,
        len(flattened_justifications),
    )
    justifications_json_data = json.dumps(flattened_justifications)
    prompt = string.Template(BULK_CATEGORIZATION_PROMPT_TEMPLATE).substitute(
        category_json_data=self._category_json_data,
        justifications_json_data=justifications_json_data,
    )

    response_text = None
    try:
      analyzer = service.registry.get(apis.LlmApiClient)
      response_text = analyzer.analyze_content(prompt)

      # Gemini might return markdown code blocks, strip them if needed
      cleaned_response = markdown.strip_markdown_code_blocks(response_text)

      categorized_justifications = json.loads(cleaned_response)
      logging.debug(
          "[%s] Categorized %d justifications.",
          self._task_family,
          len(categorized_justifications),
      )

    except Exception:
      logging.error(
          "[%s] Failed to bulk categorize justifications:  \n%s",
          self._task_family,
          response_text,
      )
      raise

    self._reconstruct_dataframe(df, categorized_justifications)

  def _flatten_and_tag_justifications(
      self, df: pd.DataFrame
  ) -> list[dict[str, str]]:
    """Flattens justifications and assigns unique IDs."""
    flattened_justifications = []
    for index, row in df.iterrows():
      sentiments = row.get("sentiments")

      for s_idx, sentiment in enumerate(sentiments):
        justifications = sentiment.get("justifications")

        for j_idx, justification in enumerate(justifications):
          quote = justification.get("quote")
          if quote:
            flattend_justification = {
                "id": f"{index}_{s_idx}_{j_idx}",
                "quote": quote,
            }
            logging.debug(
                "[%s] Adding flattened and tagged justification: %s",
                self._task_family,
                flattend_justification,
            )
            flattened_justifications.append(flattend_justification)

    return flattened_justifications

  def _reconstruct_dataframe(
      self, df: pd.DataFrame, categorized_justifications: list[dict[str, str]]
  ) -> pd.DataFrame:
    """Reconstructs the DataFrame with categorized justifications.

    Args:
      df: The DataFrame to reconstruct.
      categorized_justifications: The categorized justifications.

    Returns:
      The DataFrame with categorized justifications.
    """
    category_map = {
        item["id"]: item.get("category", "[Uncategorized]")
        for item in categorized_justifications
    }

    for index, row in df.iterrows():
      sentiments = row.get("sentiments")
      updated_sentiments = []

      for s_idx, sentiment in enumerate(sentiments):
        justifications = sentiment.get("justifications")
        updated_justifications = []

        for j_idx, justification in enumerate(justifications):
          # Re-generate the ID to lookup the category
          justification_id = f"{index}_{s_idx}_{j_idx}"

          justification["category"] = category_map.get(
              justification_id, "[Uncategorized]"
          )
          logging.debug(
              "[%s] Adding categorized justification: %s",
              self._task_family,
              justification,
          )
          updated_justifications.append(justification)

        sentiment["justifications"] = updated_justifications
        updated_sentiments.append(sentiment)

      df.at[index, "sentiments"] = updated_sentiments

    return df


class ProcessJustificationsTask(tasks_core.SentimentTask):
  """Task to process sentiment analysis justifications and categorize them.

  This task will take the raw sentiment data and the generated categories
  from the upstream tasks. It loads the created category definitions and
  processes the sentiment justifications in batches, using the LLM to
  apply the matching category to each individual quote. Finally, it writes
  the categorized justifications back into the output dataset.
  """

  def requires(self) -> dict[str, luigi.Task]:
    """Require both the raw sentiment data AND the generated categories."""
    return {
        "sentiment_data": self.my_required_task,
        "categories": GenerateJustificationCategoriesTask(
            execution_id=self.execution_id,
            my_required_task=self.my_required_task,
        ),
    }

  def run(self) -> None:
    """Executes the sentiment analysis job."""
    logging.info(
        "[%s] Starting justification processing task for execution ID: %s",
        self.task_family,
        self.execution_id,
    )

    inputs = self.input()
    sentiment_data_target = inputs["sentiment_data"]
    input_sentiment_data = sentiment_data_target.load_sentiment_data()

    self._validate_input_data(input_sentiment_data)

    try:
      categories_target = inputs["categories"]
      categories_df = categories_target.load_sentiment_data()
      category_json_data = categories_df.iloc[0]["category_json_data"]

      logging.info("Category description data loaded")

      if category_json_data == "[]":
        logging.info(
            "[%s] No categories generated upstream, skipping categorization.",
            self.task_family,
        )
        self.output().write_sentiment_data(input_sentiment_data)
        return

      categorizer = JustificationCategorizer(
          category_json_data=category_json_data, task_family=self.task_family
      )

      processed_chunks = []

      for start in range(
          0, len(input_sentiment_data), MAX_JUSTIFICATIONS_PER_BATCH
      ):
        end = start + MAX_JUSTIFICATIONS_PER_BATCH
        chunk = input_sentiment_data.iloc[start:end].copy()

        logging.info(
            "[%s] Processing batch %d to %d (total: %d)",
            self.task_family,
            start,
            end,
            len(input_sentiment_data),
        )

        # Only process rows where the relevance score is above the minimum
        # threshold for sentiment to be generated.
        relevant_mask = (
            chunk["relevanceScore"]
            >= constants.MIN_RELEVANCE_THRESHOLD_FOR_SENTIMENT_TO_BE_GENERATED
        )
        chunk_to_process = chunk[relevant_mask].copy()

        if not chunk_to_process.empty:
          categorizer.categorize(chunk_to_process)
          chunk.loc[relevant_mask, "sentiments"] = chunk_to_process[
              "sentiments"
          ]

        processed_chunks.append(chunk)

      # Combine processed chunks back into a single DataFrame
      if processed_chunks:
        input_sentiment_data = pd.concat(processed_chunks)

      self.output().write_sentiment_data(input_sentiment_data)

      logging.info(
          "[%s] Successfully generated and saved %d prompts.",
          self.task_family,
          len(input_sentiment_data),
      )

    except Exception as e:  # pylint: disable=broad-exception-caught
      logging.exception(
          "[%s] Task failed during execution %s due to %s: %s",
          self.task_family,
          self.execution_id,
          type(e).__name__,
          e,
      )
      raise

  def _validate_input_data(self, df: pd.DataFrame) -> None:
    """Validates that the input DataFrame has the expected structure.

    Args:
      df: The DataFrame to validate.
    """
    if "sentiments" not in df.columns:
      raise ValueError(
          f"[{self.task_family}] input dataFrame missing "
          "'sentiments' column."
      )
