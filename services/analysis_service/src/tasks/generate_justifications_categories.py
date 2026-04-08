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
import time

import pandas as pd
from socialpulse_common import service
from socialpulse_common.messages import workflow_execution as wfe
from socialpulse_common.utils import markdown
from tasks import core as tasks_core
from tasks.ports import apis


logger = logging.getLogger(__name__)


class JustificationCategoryGenerator:
  """Generates justification categories using an LLM."""

  MAX_JUSTIFICATIONS_PER_BATCH = 750

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

  CONSOLIDATION_PROMPT_TEMPLATE = """
  You are an expert sentiment analyst. Your goal is to consolidate a list of
  sentiment categories that were generated from different batches of customer
  feedback.

  # Input Data
  A JSON list of candidate categories generated from different batches:
  ${candidate_categories_json}

  # Goal
  Merge similar categories, remove duplicates, and produce a single set of
  mutually exclusive categories that cover the full scope of feedback.
  Ensure every category has a clear definition and a representative example.

  # Output Format
  Please provide the results in a structured JSON list:
  - **categoryName:** (e.g., "General: Brand Trust" or "Feature: Video Editing")
  - **definition:** A brief explanation of what types of quotes belong here.
  - **classificationType:** (General Sentiment OR Feature Specific)
  - **representativeExample:** A quote from the provided data that illustrates
    this category.

  Return ONLY valid JSON.
  """

  def __init__(
      self,
      analyzer: apis.LlmApiClient,
      task_family: str,
      workflow_exec: wfe.WorkflowExecutionParams,
  ):
    self.analyzer = analyzer
    self.task_family = task_family
    self.workflow_exec = workflow_exec

  def generate(self, df: pd.DataFrame) -> str:
    """Generates a list of categories based on the provided justifications.

    Args:
      df: DataFrame containing sentiment data with 'sentiments' column.

    Returns:
      JSON string of categories.
    """
    self._validate_input_data(df)

    all_justifications = self._extract_quote_data(df)
    if not all_justifications:
      logging.info(
          "[%s] No justifications found to generate categories from.",
          self.task_family,
      )
      return "[]"

    batches = [
        all_justifications[i : i + self.MAX_JUSTIFICATIONS_PER_BATCH]
        for i in range(
            0, len(all_justifications), self.MAX_JUSTIFICATIONS_PER_BATCH
        )
    ]
    logging.info(
        "[%s] Split %d justifications into %d batches.",
        self.task_family,
        len(all_justifications),
        len(batches),
    )

    candidate_categories = []
    for idx, batch in enumerate(batches):
      response_text = self._process_batch_with_retry(
          idx, len(batches), batch
      )
      self._parse_response_into_categories(
          response_text, candidate_categories, idx
      )

    if not candidate_categories:
      logging.error("[%s] No candidate categories generated.", self.task_family)
      return "[]"

    logging.info(
        "[%s] Consolidating %d candidate categories.",
        self.task_family,
        len(candidate_categories),
    )
    return self._consolidate_categories(candidate_categories)

  def _validate_input_data(self, df: pd.DataFrame) -> None:
    """Validates that the input DataFrame has the expected structure.

    Args:
      df: DataFrame containing sentiment data with 'sentiments' column.

    Raises:
      ValueError: If the input DataFrame is missing the 'sentiments' column.
    """
    if "sentiments" not in df.columns:
      raise ValueError(
          f"[{self.task_family}] input dataFrame missing "
          "'sentiments' column."
      )

  def _extract_quote_data(self, df: pd.DataFrame) -> list[dict[str, str]]:
    """Extracts justification data including quote, sentiment, and summary.

    Args:
      df: DataFrame containing sentiment data with 'sentiments' column.

    Returns:
      List of justification data.
    """
    all_justifications = []
    for _, row in df.iterrows():
      sentiments = row.get("sentiments")

      for sentiment in sentiments:
        justifications = sentiment.get("justifications")
        if justifications is None or len(justifications) == 0:
          continue

        for justification in justifications:
          quote = justification.get("quote")
          if not quote:
            continue
          item = {
              "quote": quote,
              "sentimentScore": sentiment.get("sentimentScore"),
              "summary": row.get("summary"),
          }
          all_justifications.append(item)
    return all_justifications

  def _process_batch_with_retry(
      self, idx: int, total_batches: int, batch: list[dict[str, str]]
  ) -> str:
    """Processes a single batch of justifications with retry logic.

    Args:
      idx: Index of the batch.
      total_batches: Total number of batches.
      batch: List of justification data.

    Returns:
      JSON string of categories.
    """
    logging.info(
        "[%s] Processing batch %d/%d (%d items).",
        self.task_family,
        idx + 1,
        total_batches,
        len(batch),
    )
    batch_json_data = json.dumps(batch)
    template = string.Template(self.CATEGORY_GENERATION_PROMPT_TEMPLATE)
    prompt = template.substitute(justification_json_data=batch_json_data)

    # Retry logic: wait 1 second to retry once.
    try:
      return self.analyzer.analyze_content(prompt)
    except Exception as e:  # pylint: disable=broad-exception-caught
      logging.warning(
          "[%s] Batch %d failed: %s. Retrying in 1 second...",
          self.task_family,
          idx + 1,
          e,
      )

      time.sleep(1)
      try:
        return self.analyzer.analyze_content(prompt)
      except Exception as e_retry:
        logging.error(
            "[%s] Batch %d failed on retry: %s.",
            self.task_family,
            idx + 1,
            e_retry,
        )
        raise

  def _parse_response_into_categories(
      self,
      response_text: str,
      justification_categories: list[dict[str, str]],
      idx: int,
  ):
    """Parses the response from the LLM into categories.

    Args:
      response_text: JSON string of categories.
      justification_categories: List of justification categories.
      idx: Index of the batch for logging.
    """
    cleaned_response = markdown.strip_markdown_code_blocks(response_text)
    try:
      batch_categories = json.loads(cleaned_response)
      if isinstance(batch_categories, list):
        justification_categories.extend(batch_categories)
      else:
        logging.warning(
            "[%s] Batch %d did not return a list: %s",
            self.task_family,
            idx + 1,
            response_text,
        )
    except json.JSONDecodeError:
      logging.warning(
          "[%s] Failed to parse JSON for batch %d: %s",
          self.task_family,
          idx + 1,
          response_text,
      )
      raise

  def _consolidate_categories(
      self, candidate_categories: list[dict[str, str]]
  ) -> str:
    """Consolidates candidate categories using an LLM.

    Args:
      candidate_categories: List of candidate categories.

    Returns:
      JSON string of consolidated categories.
    """
    candidate_categories_json = json.dumps(candidate_categories)
    consolidation_prompt = string.Template(
        self.CONSOLIDATION_PROMPT_TEMPLATE
    ).substitute(candidate_categories_json=candidate_categories_json)

    try:
      final_response_text = self.analyzer.analyze_content(consolidation_prompt)
    except Exception as e:
      logging.error(
          "[%s] Failed to consolidate categories: %s", self.task_family, e
      )
      raise

    cleaned_final_response = markdown.strip_markdown_code_blocks(
        final_response_text
    )
    return cleaned_final_response


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

    analyzer = service.registry.get(apis.LlmApiClient)
    generator = JustificationCategoryGenerator(
        analyzer, self.task_family, self.workflow_exec
    )

    try:
      category_json_data = generator.generate(input_sentiment_data)
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
