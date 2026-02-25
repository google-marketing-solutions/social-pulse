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

"""Module for background generation and storage of report insights."""

import json
import logging
from typing import Any

from domain import sentiment_report
from socialpulse_common.messages import report_insight as insight_msg
from socialpulse_common.messages import sentiment_report as report_msg

logger = logging.getLogger(__name__)


def generate_and_store_insights(
    report_id: str,
    datasets: list[report_msg.SentimentReportDataset],
    app_config: Any,
) -> None:
  """Generates insights using Gemini and stores them in the database.

  Args:
    report_id: The ID of the report.
    datasets: The datasets associated with the report.
    app_config: The application configuration containing dependencies.
  """
  try:
    logger.info(
        "Starting background insight generation for report %s", report_id
    )

    # 1. Fetch report entity
    report_entity: sentiment_report.SentimentReportEntity = (
        app_config.sentiment_report_repository.load_report(report_id)
    )

    # 2. Fetch analysis results from BigQuery
    analysis_results = app_config.dataset_repository.get_analysis_results(
        datasets,
        include_justifications=report_entity.include_justifications,
    )

    analysis_dict = analysis_results.model_dump(exclude_none=True)
    if not analysis_dict:
      logger.warning(
          "No analysis results found for report %s. Skipping insights.",
          report_id
      )
      return

    # 3. Construct the report context string
    report_context = json.dumps(analysis_dict, default=str)

    # 4. Generate Base Insights (Top Trends)
    logger.debug("Generating base insights for report %s", report_id)
    trends_json, trends_raw = (
        app_config.gemini_insights_provider.generate_base_insights(
            report_context
        )
    )

    if trends_json:
      app_config.report_insights_repository.insert_insight(
          report_id=report_id,
          insight_type=insight_msg.InsightType.TREND,
          content=trends_json,
          raw_prompt_output=trends_raw,
      )

    # 5. Generate Spike Analysis
    logger.debug("Generating spike analysis for report %s", report_id)
    spikes_json, spikes_raw = (
        app_config.gemini_insights_provider.generate_spike_analysis(
            report_context
        )
    )

    if spikes_json:
      app_config.report_insights_repository.insert_insight(
          report_id=report_id,
          insight_type=insight_msg.InsightType.SPIKE,
          content=spikes_json,
          raw_prompt_output=spikes_raw,
      )

    logger.info(
        "Successfully generated and stored insights for report %s",
        report_id
    )

  except Exception as e:  # pylint: disable=broad-except
    # Gracefully handle the error without bubbling up the background task
    logger.exception(
        "Failed to generate and store insights for report %s: %s",
        report_id,
        str(e)
    )
