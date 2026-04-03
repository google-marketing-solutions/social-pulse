#  Copyright 2026 Google LLC
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

"""Task to consolidate brands and products in a SOV report using an LLM."""

import json
import logging
import string

import pandas as pd
from socialpulse_common import service
from tasks import core as tasks_core
from tasks.ports import apis


logger = logging.getLogger(__name__)

CONSOLIDATION_PROMPT_TEMPLATE = """
  As an expert market analyst, analyze the following list of brands and
  products extracted from social sentiment data.
  Your task is to consolidate them into a mapping of unique, top-level
  parent brands.

  For example, if the list includes "Google", "Gemini", and "Veo", they
  should all map to "Google" as the top-level brand.

  Please provide the output as a valid JSON object where keys are the
  original brand/product names from the provided list, and values are
  the consolidated top-level brand names.

  List of Brands and Products:
  ${brands_products_list}

  Output Format:
  {
    "originalName": "consolidatedName"
  }
"""


class GenerateConsolidatedBrandsTask(tasks_core.SentimentTask):
  """Task to consolidate brands and products into a top level brand."""

  def run(self) -> None:
    """Executes the consolidation job."""
    logging.info(
        "[%s] Consolidating brands and products for execution ID: %s",
        self.task_family,
        self.execution_id,
    )

    input_target = self.input()
    input_sentiment_data = input_target.load_sentiment_data()
    self._validate_input_data(input_sentiment_data)

    list_of_brands_and_products = self._extract_brands(input_sentiment_data)

    if not list_of_brands_and_products:
      logging.info(
          "[%s] No brands or products found to consolidate.",
          self.task_family,
      )
      self.output().write_sentiment_data(
          pd.DataFrame([{"consolidated_brands_json": "{}"}])
      )
      return

    try:
      template = string.Template(CONSOLIDATION_PROMPT_TEMPLATE)
      prompt = template.substitute(
          brands_products_list=json.dumps(list_of_brands_and_products)
      )

      analyzer = service.registry.get(apis.LlmApiClient)
      consolidated_json = analyzer.analyze_content(prompt)

      df = pd.DataFrame([{"consolidated_brands_json": consolidated_json}])
      self.output().write_sentiment_data(df)

      logging.info(
          "[%s] Successfully consolidated brands.", self.task_family
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

  def _extract_brands(self, df: pd.DataFrame) -> list[str]:
    """Extracts brands and products from the input DataFrame.

    Args:
      df: The DataFrame to extract the brands and products from.

    Returns:
      A list of strings containing the brands and products.
    """
    if df.empty or "sentiments" not in df.columns:
      return []

    exploded = df.explode("sentiments")
    exploded = exploded.dropna(subset=["sentiments"])

    def extract_product_or_brand(sentiment):
      if isinstance(sentiment, dict):
        return sentiment.get("productOrBrand")
      return None
    brands = exploded["sentiments"].apply(extract_product_or_brand)

    unique_brands = brands.dropna().unique().tolist()
    unique_brands = [
        b.strip() for b in unique_brands if isinstance(b, str) and b.strip()
    ]
    unique_brands = list(dict.fromkeys(unique_brands))

    return unique_brands
