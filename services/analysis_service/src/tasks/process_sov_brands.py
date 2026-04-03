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

"""Task to map brands and products to top-level brands."""

import json
import logging

import luigi
import pandas as pd
from tasks import core as tasks_core
from tasks.generate_products_brands_lookup import GenerateConsolidatedBrandsTask


logger = logging.getLogger(__name__)


class ProcessSovBrandsTask(tasks_core.SentimentTask):
  """Task to map brands and products to top-level brands."""

  def requires(self) -> dict[str, luigi.Task]:
    """Require both the raw sentiment data AND the generated categories."""
    return {
        "sentiment_data": self.my_required_task,
        "consolidated_brands": GenerateConsolidatedBrandsTask(
            execution_id=self.execution_id,
            my_required_task=self.my_required_task,
        ),
    }

  def run(self) -> None:
    logging.info(
        "[%s] Processing SOV brands for execution ID: %s",
        self.task_family,
        self.execution_id,
    )

    inputs = self.input()
    sentiment_data = inputs["sentiment_data"].load_sentiment_data()
    consolidated_brands = inputs["consolidated_brands"].load_sentiment_data()

    self._validate_input_data(sentiment_data)

    if consolidated_brands.empty:
      logging.info(
          "[%s] No consolidated brands data found.", self.task_family
      )
      self.output().write_sentiment_data(sentiment_data)
      return

    consolidated_json = consolidated_brands.iloc[0]["consolidated_brands_json"]
    try:
      consolidated_dict = json.loads(consolidated_json)
    except json.JSONDecodeError:
      logging.error(
          "[%s] Failed to parse consolidated brands JSON.", self.task_family
      )
      self.output().write_sentiment_data(sentiment_data)
      return

    for index, row in sentiment_data.iterrows():
      sentiments = row.get("sentiments")
      if not isinstance(sentiments, list):
        continue

      updated_sentiments = []
      for sentiment in sentiments:
        if isinstance(sentiment, dict):
          current_brand = sentiment.get("productOrBrand")
          if current_brand and current_brand in consolidated_dict:
            sentiment["productOrBrand"] = consolidated_dict[current_brand]
        updated_sentiments.append(sentiment)

      sentiment_data.at[index, "sentiments"] = updated_sentiments

    self.output().write_sentiment_data(sentiment_data)
    logging.info(
        "[%s] Successfully processed SOV brands.", self.task_family
    )

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
