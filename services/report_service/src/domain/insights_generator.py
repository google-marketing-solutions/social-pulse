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
from socialpulse_common.messages import common as msg_common
from socialpulse_common.messages import report_insight as insight_msg

logger = logging.getLogger(__name__)


def _get_top_15_brands(
    report: sentiment_report.SentimentReportEntity,
    app_config: Any,
) -> list[str]:
  """Retrieves the top 15 brands by aggregated views for the report.

  Args:
    report: The SentimentReportEntity.
    app_config: The application configuration.

  Returns:
    A list of at most 15 brand name strings.
  """
  table_id = report.get_bq_table_id_for_source(
      msg_common.SocialMediaSource.YOUTUBE_VIDEO)
  if not table_id:
    return []

  try:
    sov_results = app_config.dataset_repository.query_share_of_voice(
        table_id=table_id,
        relevance_threshold=report.relevance_threshold,
    )
    top_brands = [
        row["productOrBrand"]
        for row in sov_results
        if row.get("productOrBrand")
    ]
    # Deduplicate (preserving order) and slice to top 15
    return list(dict.fromkeys(top_brands))[:15]
  except Exception as e:  # pylint: disable=broad-except
    logger.warning("Failed to query Share of Voice for table %s: %s", table_id,
                   e)
    return []


def generate_and_store_insights(
    report: sentiment_report.SentimentReportEntity,
    app_config: Any,
) -> None:
  """Generates insights using Gemini and stores them in the database.

  Args:
    report: The SentimentReportEntity.
    app_config: The application configuration containing dependencies.

  Returns:
    None.

  Raises:
    Exception: If insight generation fails.
  """
  report_id = report.entity_id
  try:
    logger.info("Starting background insight generation for report %s",
                report_id)

    # 1. Check sources
    if msg_common.SocialMediaSource.YOUTUBE_VIDEO not in report.sources:
      logger.warning(
          "Report %s does not have YOUTUBE_VIDEO source. Skipping insights.",
          report_id)
      return

    # 2. Fetch analysis results from BigQuery
    # Filter datasets to only include YouTube Video context
    filtered_datasets = [
        d for d in report.datasets
        if d.source == msg_common.SocialMediaSource.YOUTUBE_VIDEO
    ]
    analysis_results = app_config.dataset_repository.get_full_report_context(
        filtered_datasets)

    if not analysis_results:
      logger.warning(
          "No analysis results found for report %s. Skipping insights.",
          report_id)
      return

    # 3. Construct the report context string
    report_context = json.dumps(analysis_results,
                                default=str,
                                separators=(",", ":"))

    # 4. Determine top brands for SHARE_OF_VOICE reports
    is_sov_report = (msg_common.SentimentDataType.SHARE_OF_VOICE
                     in report.data_outputs)
    top_15_brands = []
    if is_sov_report:
      top_15_brands = _get_top_15_brands(report, app_config)

    # 5. Generate Base Insights (Top Trends)
    logger.debug("Generating base insights for report %s", report_id)
    trends_json, trends_raw = (
        app_config.gemini_insights_provider.generate_base_insights(
            report_context=report_context,
            top_brands=top_15_brands if is_sov_report else None,
        ))

    if trends_json:
      app_config.report_insights_repository.insert_insight(
          report_id=report_id,
          insight_type=insight_msg.InsightType.TREND,
          content=trends_json,
          raw_prompt_output=trends_raw,
      )

    # 6. Generate Spike Analysis
    logger.debug("Generating spike analysis for report %s", report_id)
    spikes_json, spikes_raw = (app_config.gemini_insights_provider.
                               generate_spike_analysis(report_context))

    if spikes_json:
      app_config.report_insights_repository.insert_insight(
          report_id=report_id,
          insight_type=insight_msg.InsightType.SPIKE,
          content=spikes_json,
          raw_prompt_output=spikes_raw,
      )

    logger.info("Successfully generated and stored insights for report %s",
                report_id)

  except Exception as e:  # pylint: disable=broad-except
    # Gracefully handle the error without bubbling up the background task
    logger.exception("Failed to generate and store insights for report %s: %s",
                     report_id, str(e))
