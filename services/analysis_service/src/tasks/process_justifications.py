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

import pandas as pd
from socialpulse_common import service
from tasks import constants
from tasks import core as tasks_core
from tasks.ports import apis


logger = logging.getLogger(__name__)

MAX_JUSTIFICATIONS_PER_BATCH = 250

CATEGORY_GENERATION_PROMPT_TEMPLATE = """
  # Methodology: Chain of Thought
  You must follow these steps internally before providing your final output:
  1. **Holistic Review:** Scan every quote and summary in the JSON list to
     understand the full scope of feedback.
  2. **Sentiment Stratification:** Distinguish between "General Sentiment"
     (broad statements about brand, reliability, or quality) and
     "Feature/Aspect Specific" (mentions of specific tools, buttons, or
     workflows).
  3. **Thematic Clustering:** Group similar ideas. For example, if multiple
     quotes mention "Magic Wand" or "Auto-Enhance," create a feature-specific
     category for "AI Tools."
  4. **Final Refinement:** Ensure categories are mutually exclusive. Each
     category should have a clear definition so that a quote can be easily
     mapped to it later.

  # Classification Criteria
  Your categories must include:
  - **General Sentiment Categories:** Focused on the "How" or "Why" (e.g.,
    "High Reliability," "Community Connection," "Ease of Use").
  - **Feature Specific Categories:** Focused on the "What" (e.g.,
    "Feature: Magic Video Editor," "Feature: UI Customization").

  # Output Format
  Please provide the results in a structured JSON list:
  - **categoryName:** (e.g., "General: Brand Trust" or "Feature: Video Editing")
  - **definition:** A brief explanation of what types of quotes belong here.
  - **classificationType:** (General Sentiment OR Feature Specific)
  - **representativeExample:** A quote from the provided data that illustrates
    this category.

  # Data for Analysis
  ${justification_json_data}
  """

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
      task_family: str = "JustificationCategorizer"
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
      raise ValueError("No justifications to categorize.")

    logging.debug(
        "[%s] Flattened %d justifications.", self._task_family,
        len(flattened_justifications)
    )
    justifications_json_data = json.dumps(flattened_justifications)
    prompt = string.Template(BULK_CATEGORIZATION_PROMPT_TEMPLATE).substitute(
        category_json_data=self._category_json_data,
        justifications_json_data=justifications_json_data
    )

    response_text = None
    try:
      analyzer = service.registry.get(apis.LlmApiClient)
      response_text = analyzer.analyze_content_with_gemini(prompt)

      # Gemini might return markdown code blocks, strip them if needed
      cleaned_response = response_text.strip()
      if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response[7:]
      if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-3]

      categorized_justifications = json.loads(cleaned_response)
      logging.debug(
          "[%s] Categorized %d justifications.", self._task_family,
          len(categorized_justifications)
      )

    except Exception:
      logging.error(
          "[%s] Failed to bulk categorize justifications:  \n%s",
          self._task_family, response_text
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
                self._task_family, flattend_justification
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
              "[%s] Adding categorized justification: %s", self._task_family,
              justification
          )
          updated_justifications.append(justification)

        sentiment["justifications"] = updated_justifications
        updated_sentiments.append(sentiment)

      df.at[index, "sentiments"] = updated_sentiments

    return df


class ProcessJustificationsTask(tasks_core.SentimentTask):
  """Task to process the sentiment analysis justifications and categorize them.

  This task will take the justifications from the sentiment analysis job and
  categorize them.  It will prompt the LLM to generate categories from all of
  the combined justifications, and then setup the output dataset with a prompt
  to categorize each justification in a request row.  Then another batch job
  will be run to categorize each justification.
  """

  def run(self) -> None:
    """Executes the sentiment analysis job."""
    logging.info(
        "[%s] Starting justification processing task for execution ID: %s",
        self.task_family,
        self.execution_id,
    )

    input_target = self.input()
    input_sentiment_data = input_target.load_sentiment_data()

    self._validate_input_data(input_sentiment_data)

    try:
      category_json_data = self._generate_category_description_json_data(
          input_sentiment_data
      )
      logging.info("Category description data: %s", category_json_data)

      categorizer = JustificationCategorizer(
          category_json_data=category_json_data,
          task_family=self.task_family
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
          chunk.loc[relevant_mask, "sentiments"] = (
              chunk_to_process["sentiments"]
          )

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

  def _generate_category_description_json_data(self, df: pd.DataFrame) -> str:
    """Generates a list of categories based on the provided justifications.

    Args:
      df: The DataFrame to extract the quote data from.

    Returns:
      A list of dictionaries containing the quote data.
    """
    all_justifications = self._extract_quote_data(df)
    if not all_justifications:
      raise ValueError("No justifications found to generate categories from.")

    justification_json_data = json.dumps(all_justifications)
    template = string.Template(CATEGORY_GENERATION_PROMPT_TEMPLATE)
    prompt = template.substitute(
        justification_json_data=justification_json_data
    )

    analyzer = service.registry.get(apis.LlmApiClient)
    return analyzer.analyze_content_with_gemini(prompt)

  def _extract_quote_data(self, df: pd.DataFrame) -> list[dict[str, str]]:
    """Extracts justification data including quote, sentiment, and summary.

    Args:
      df: The DataFrame to extract the quote data from.

    Returns:
      A list of dictionaries containing the quote data.
    """
    all_justifications = []

    # We assume validated structure, but handle empty lists safely
    for _, row in df.iterrows():
      sentiments = row.get("sentiments")

      for sentiment in sentiments:
        for justification in sentiment.get("justifications", []):
          if quote := justification.get("quote"):

            item = {
                "quote": quote,
                "sentimentScore": sentiment.get("sentimentScore"),
                "summary": row.get("summary"),
            }
            all_justifications.append(item)

    logging.info(
        "[%s] Found %d justifications to categorize.", self.task_family,
        len(all_justifications)
    )
    return all_justifications
