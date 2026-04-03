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

"""Task to generate justification categories using an LLM."""

import json
import logging
import string

import pandas as pd
from socialpulse_common import service
from tasks import core as tasks_core
from tasks.ports import apis


logger = logging.getLogger(__name__)

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


class GenerateJustificationCategoriesTask(tasks_core.SentimentTask):
  """Task to generate justification categories using an LLM."""

  def run(self) -> None:
    """Executes the category generation job."""
    logging.info(
        "[%s] Generating categories for execution ID: %s",
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
      logging.info("Category description data generated")

      # Store the category JSON string in a simple 1-row DataFrame
      # This satisfies the existing SentimentDataRepoTarget interface
      category_df = pd.DataFrame([{"category_json_data": category_json_data}])

      self.output().write_sentiment_data(category_df)

      logging.info(
          "[%s] Successfully generated and saved categories.",
          self.task_family,
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
      logging.info(
          "[%s] No justifications found to generate categories from.",
          self.task_family,
      )
      return "[]"

    justification_json_data = json.dumps(all_justifications)
    template = string.Template(CATEGORY_GENERATION_PROMPT_TEMPLATE)
    prompt = template.substitute(
        justification_json_data=justification_json_data
    )

    analyzer = service.registry.get(apis.LlmApiClient)
    return analyzer.analyze_content(prompt)

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
        "[%s] Found %d justifications to categorize.",
        self.task_family,
        len(all_justifications),
    )
    return all_justifications
