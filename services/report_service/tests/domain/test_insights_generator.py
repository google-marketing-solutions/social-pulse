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

"""Unit tests for the insights_generator module.

These tests assert that the background task logic correctly fetches report
context, calls the Gemini provider, and persists the generated insights.
"""

import datetime
import unittest
from unittest import mock

from domain import insights_generator
from domain import sentiment_report
from socialpulse_common.messages import common as common_msg
from socialpulse_common.messages import report_insight as insight_msg
from socialpulse_common.messages import sentiment_report as report_msg


class TestInsightsGenerator(unittest.TestCase):
  """Test suite for the generate_and_store_insights function."""

  def setUp(self):
    super().setUp()
    self.report_id = "test-report-id"

    self.datasets = [
        report_msg.SentimentReportDataset(
            report_id=self.report_id,
            source=common_msg.SocialMediaSource.YOUTUBE_COMMENT,
            data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
            dataset_uri="bq://test-project.dataset.table"
        )
    ]

    self.app_config = mock.MagicMock()

    self.report_entity = sentiment_report.SentimentReportEntity(
        report_id=self.report_id,
        topic="Test Topic",
        status=report_msg.Status.COMPLETED,
        sources=[common_msg.SocialMediaSource.YOUTUBE_COMMENT],
        data_outputs=[common_msg.SentimentDataType.SENTIMENT_SCORE],
        include_justifications=True,
        start_time=datetime.datetime(2026, 1, 1),
        end_time=datetime.datetime(2026, 1, 31),
        datasets=self.datasets
    )

    # Configure the load_report mock
    report_repo = self.app_config.sentiment_report_repository
    report_repo.load_report.return_value = self.report_entity

    # Mock BigQuery result
    self.mock_analysis_result = report_msg.AnalysisResults(
        youtube_comment=report_msg.SourceAnalysisResult()
    )

    dataset_repo = self.app_config.dataset_repository
    dataset_repo.get_analysis_results.return_value = self.mock_analysis_result

  def test_generate_and_store_insights_success(self):
    """Tests the successful generation and persistence of insights.

    Given a report with existing analysis results
    When the generate_and_store_insights orchestrator is called
    Then the Gemini provider generates both Base Insights and Spike Analysis
    and the ReportInsights repository inserts them.
    """
    # Mock successful Gemini generations
    gemini_provider = self.app_config.gemini_insights_provider
    gemini_provider.generate_base_insights.return_value = (
        {"top_trends": []}, "trends_raw"
    )
    gemini_provider.generate_spike_analysis.return_value = (
        {"spikes": []}, "spikes_raw"
    )

    insights_generator.generate_and_store_insights(
        report_id=self.report_id,
        datasets=self.datasets,
        app_config=self.app_config
    )

    # Verify BigQuery data was fetched
    dataset_repo = self.app_config.dataset_repository
    dataset_repo.get_analysis_results.assert_called_once_with(
        self.datasets,
        include_justifications=True
    )

    # Verify Gemini provider was called twice
    gemini_provider.generate_base_insights.assert_called_once()
    gemini_provider.generate_spike_analysis.assert_called_once()

    # Verify insights were inserted into the database twice
    insights_repo = self.app_config.report_insights_repository
    self.assertEqual(
        insights_repo.insert_insight.call_count,
        2
    )

    # Check specific calls for insert
    insights_repo.insert_insight.assert_any_call(
        report_id=self.report_id,
        insight_type=insight_msg.InsightType.TREND,
        content={"top_trends": []},
        raw_prompt_output="trends_raw"
    )
    insights_repo.insert_insight.assert_any_call(
        report_id=self.report_id,
        insight_type=insight_msg.InsightType.SPIKE,
        content={"spikes": []},
        raw_prompt_output="spikes_raw"
    )

  def test_generate_and_store_insights_no_analysis_data(self):
    """Tests the insights generator does not proceed if no data exists.

    Given a report where BigQuery returns no analysis results
    When generate_and_store_insights is called
    Then the background task returns early without calling Gemini or inserting.
    """
    dataset_repo = self.app_config.dataset_repository
    dataset_repo.get_analysis_results.return_value = (
        report_msg.AnalysisResults()
    )

    insights_generator.generate_and_store_insights(
        report_id=self.report_id,
        datasets=self.datasets,
        app_config=self.app_config
    )

    # Verify Gemini provider was NOT called
    gemini_provider = self.app_config.gemini_insights_provider
    gemini_provider.generate_base_insights.assert_not_called()
    gemini_provider.generate_spike_analysis.assert_not_called()

    # Verify nothing was inserted
    insights_repo = self.app_config.report_insights_repository
    insights_repo.insert_insight.assert_not_called()

  def test_generate_insights_handles_exceptions_gracefully(self):
    """Tests that exceptions thrown by Gemini APIs are caught safely.

    Given a report with data analysis
    When the Gemini provider raises an exception
    Then the error is caught, logged, and the function exits without raising.
    """
    gemini_provider = self.app_config.gemini_insights_provider
    gemini_provider.generate_base_insights.side_effect = Exception(
        "API Failed"
    )

    # Call function, should not raise an exception
    insights_generator.generate_and_store_insights(
        report_id=self.report_id,
        datasets=self.datasets,
        app_config=self.app_config
    )

    # Verify it attempted to call the base insights API but stopped there
    gemini_provider.generate_base_insights.assert_called_once()
    insights_repo = self.app_config.report_insights_repository
    insights_repo.insert_insight.assert_not_called()


if __name__ == "__main__":
  unittest.main()
