# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for the CompositeAnalysisResultsBuilder."""

import unittest
from unittest import mock

from domain import sentiment_report
from domain.analysis_results import builder
from domain.analysis_results import core as builder_core
from socialpulse_common.messages import analysis_result
from socialpulse_common.messages import common as common_msg
from socialpulse_common.messages import sentiment_report as report_msg


class CompositeAnalysisResultsBuilderTest(unittest.TestCase):
  """Tests for CompositeAnalysisResultsBuilder."""

  def setUp(self):
    super().setUp()
    self.builder = builder.CompositeAnalysisResultsBuilder()
    self.start_date = "2023-01-01"
    self.end_date = "2023-01-31"

  def test_build_results_succeeds_and_merges_data(self):
    """Succeeds and deeply merges results from mocked builders.

    Given report datasets and mocked builders that return partial results.
    When build_results is called.
    Then the returned dictionary contains deep-merged results from all builders.
    """
    dataset = report_msg.SentimentReportDataset(
        report_id="report_123",
        source=common_msg.SocialMediaSource.YOUTUBE_VIDEO,
        data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
        dataset_uri="gs://bucket/data.json",
    )

    mock_builder_1 = mock.create_autospec(builder_core.ResultDataBuilder)
    mock_builder_1.build.return_value = (
        analysis_result.SentimentOverTimeResultSet(
            sentiment_over_time=[
                analysis_result.SentimentDataPoint(
                    date="2023-01-01", positive=10, negative=0, neutral=0
                )
            ]
        )
    )

    mock_builder_2 = mock.create_autospec(builder_core.ResultDataBuilder)
    mock_builder_2.build.return_value = (
        analysis_result.OverallSentimentResultSet(
            overall_sentiment=analysis_result.OverallSentimentDataPoint(
                positive=50, negative=0, neutral=0, average=1.0, item_count=100
            )
        )
    )

    report_entity = mock.create_autospec(
        sentiment_report.SentimentReportEntity, instance=True
    )
    report_entity.datasets = [dataset]

    with mock.patch.object(
        self.builder,
        "_get_builders_for_dataset",
        return_value=[mock_builder_1, mock_builder_2],
    ):
      results = self.builder.build_results(
          report_entity=report_entity,
          start_date=self.start_date,
          end_date=self.end_date,
      )

    expected_results = {
        "YOUTUBE_VIDEO": {
            "sentimentOverTime": [{
                "date": "2023-01-01",
                "positive": 10,
                "negative": 0,
                "neutral": 0,
            }],
            "overallSentiment": {
                "positive": 50,
                "negative": 0,
                "neutral": 0,
                "average": 1.0,
                "itemCount": 100,
            },
        }
    }
    self.assertEqual(results, expected_results)

  def test_build_results_continues_on_builder_exception(self):
    """Succeeds and logs a warning when a builder raises an exception.

    Given mocked builders where one raises an exception and another succeeds.
    When build_results is called.
    Then the exception is caught, a warning is logged, and success continues.
    """
    dataset = report_msg.SentimentReportDataset(
        report_id="report_123",
        source=common_msg.SocialMediaSource.YOUTUBE_VIDEO,
        data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
        dataset_uri="gs://bucket/data.json",
    )

    mock_builder_1 = mock.create_autospec(builder_core.ResultDataBuilder)
    mock_builder_1.build.side_effect = ValueError("Builder failed")

    mock_builder_2 = mock.create_autospec(builder_core.ResultDataBuilder)
    mock_builder_2.build.return_value = (
        analysis_result.OverallSentimentResultSet(
            overall_sentiment=analysis_result.OverallSentimentDataPoint(
                positive=1, negative=0, neutral=0, average=1.0, item_count=1
            )
        )
    )

    report_entity = mock.create_autospec(
        sentiment_report.SentimentReportEntity, instance=True
    )
    report_entity.datasets = [dataset]

    with mock.patch.object(
        self.builder,
        "_get_builders_for_dataset",
        return_value=[mock_builder_1, mock_builder_2],
    ):
      with mock.patch.object(builder.logger, "warning") as mock_logger:
        results = self.builder.build_results(
            report_entity=report_entity,
            start_date=self.start_date,
            end_date=self.end_date,
        )

    self.assertEqual(
        results,
        {
            "YOUTUBE_VIDEO": {
                "overallSentiment": {
                    "positive": 1,
                    "negative": 0,
                    "neutral": 0,
                    "average": 1.0,
                    "itemCount": 1,
                }
            }
        },
    )
    mock_logger.assert_called_once()

  def test_build_results_with_youtube_video_timeline(self):
    """Returns correct builder results for YouTube video timeline.

    Given a dataset for Google YouTube video sentiment timeline.
    When build_results is executed.
    Then the YouTube video timeline builder is invoked and aggregated.
    """
    dataset = report_msg.SentimentReportDataset(
        report_id="report_123",
        source=common_msg.SocialMediaSource.YOUTUBE_VIDEO,
        data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
        dataset_uri="gs://bucket",
    )
    mock_bldr = mock.create_autospec(builder_core.ResultDataBuilder)
    mock_bldr.build.return_value = analysis_result.OverallSentimentResultSet(
        overall_sentiment=analysis_result.OverallSentimentDataPoint(
            positive=1, negative=0, neutral=0, average=1.0, item_count=1
        )
    )

    with mock.patch.object(
        self.builder,
        "_get_builders_for_dataset",
        return_value=[mock_bldr],
    ):
      report_entity = mock.create_autospec(
          sentiment_report.SentimentReportEntity, instance=True
      )
      report_entity.datasets = [dataset]
      results = self.builder.build_results(report_entity=report_entity)

    self.assertEqual(
        results,
        {
            "YOUTUBE_VIDEO": {
                "overallSentiment": {
                    "positive": 1,
                    "negative": 0,
                    "neutral": 0,
                    "average": 1.0,
                    "itemCount": 1,
                }
            }
        },
    )

  def test_build_results_with_youtube_video_share_of_voice(self):
    """Executes YouTube video share of voice builders.

    Given a dataset for YouTube video share of voice.
    When build_results is called.
    Then the share of voice builders are executed and aggregated.
    """
    dataset = report_msg.SentimentReportDataset(
        report_id="report_123",
        source=common_msg.SocialMediaSource.YOUTUBE_VIDEO,
        data_output=common_msg.SentimentDataType.SHARE_OF_VOICE,
        dataset_uri="gs://bucket",
    )
    mock_bldr = mock.create_autospec(builder_core.ResultDataBuilder)
    mock_bldr.build.return_value = analysis_result.ShareOfVoiceResultSet(
        share_of_voice=[
            analysis_result.ShareOfVoiceDataPoint(
                name="test", positive=1, negative=0, neutral=0
            )
        ]
    )

    with mock.patch.object(
        self.builder,
        "_get_builders_for_dataset",
        return_value=[mock_bldr],
    ):
      report_entity = mock.create_autospec(
          sentiment_report.SentimentReportEntity, instance=True
      )
      report_entity.datasets = [dataset]
      results = self.builder.build_results(report_entity=report_entity)

    self.assertEqual(
        results,
        {
            "YOUTUBE_VIDEO": {
                "shareOfVoice": [
                    {"name": "test", "positive": 1, "negative": 0, "neutral": 0}
                ]
            }
        },
    )

  def test_build_results_with_youtube_comment_timeline(self):
    """Executes YouTube comment timeline builders.

    Given a dataset for YouTube comment sentiment timeline.
    When build_results is called.
    Then the YouTube comment timeline builders are executed.
    """
    dataset = report_msg.SentimentReportDataset(
        report_id="report_123",
        source=common_msg.SocialMediaSource.YOUTUBE_COMMENT,
        data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
        dataset_uri="gs://bucket",
    )
    mock_bldr = mock.create_autospec(builder_core.ResultDataBuilder)
    mock_bldr.build.return_value = analysis_result.OverallSentimentResultSet(
        overall_sentiment=analysis_result.OverallSentimentDataPoint(
            positive=2, negative=0, neutral=0, average=1.0, item_count=2
        )
    )

    with mock.patch.object(
        self.builder,
        "_get_builders_for_dataset",
        return_value=[mock_bldr],
    ):
      report_entity = mock.create_autospec(
          sentiment_report.SentimentReportEntity, instance=True
      )
      report_entity.datasets = [dataset]
      results = self.builder.build_results(report_entity=report_entity)

    self.assertEqual(
        results,
        {
            "YOUTUBE_COMMENT": {
                "overallSentiment": {
                    "positive": 2,
                    "negative": 0,
                    "neutral": 0,
                    "average": 1.0,
                    "itemCount": 2,
                }
            }
        },
    )

  def test_build_results_with_unknown_source(self):
    """Returns empty results for unknown dataset source.

    Given a dataset with an unknown source.
    When build_results is called.
    Then an empty dictionary is returned.
    """
    dataset = report_msg.SentimentReportDataset(
        report_id="report_123",
        source=common_msg.SocialMediaSource.UNKNOWN,
        data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
        dataset_uri="gs://bucket",
    )
    report_entity = mock.create_autospec(
        sentiment_report.SentimentReportEntity, instance=True
    )
    report_entity.datasets = [dataset]
    results = self.builder.build_results(report_entity=report_entity)
    self.assertEqual(results, {"UNKNOWN": {}})


if __name__ == "__main__":
  unittest.main()
