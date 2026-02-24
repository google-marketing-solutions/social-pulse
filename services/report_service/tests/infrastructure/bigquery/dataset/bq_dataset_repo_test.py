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
"""Tests for the BigQuery Dataset Repository."""

import unittest
from unittest import mock

from infrastructure.bigquery.dataset import bq_dataset_repo
from socialpulse_common.messages import common as msg_common
from socialpulse_common.messages import sentiment_report as report_msg
from socialpulse_common.persistence import bigquery_client


class BigQueryDatasetRepoTest(unittest.TestCase):

  def setUp(self):
    super().setUp()

    self.mock_bq_client = mock.Mock(spec=bigquery_client.BigQueryClient)
    self.repo = bq_dataset_repo.BigQueryDatasetRepo(self.mock_bq_client)

  def test_get_analysis_results_skips_justifications_when_flag_is_false(self):
    # Setup
    super().setUp()

    dataset = report_msg.SentimentReportDataset(
        dataset_uri="bq://project/dataset/table",
        source=msg_common.SocialMediaSource.YOUTUBE_VIDEO,
        data_output=msg_common.SentimentDataType.SENTIMENT_SCORE
    )

    # Mock BQ responses
    # First query is for sentiment timeline/overall
    self.mock_bq_client.query.side_effect = [
        [
            {
                "published_week": "2023-01-01",
                "POSITIVE_VIEWS": 100,
                "NEGATIVE_VIEWS": 10,
                "NEUTRAL_VIEWS": 5,
                "TOTAL_VIEWS": 115
            }
        ],
        # If justifications were called, there would be more queries here.
    ]

    # Act
    results = self.repo.get_analysis_results(
        [dataset],
        include_justifications=False
    )

    # Assert
    # Verify ONLY the sentiment score query was made
    # (excluding justification queries)
    # The implementation makes:
    # 1. _query_sentiment_score
    # 2. _query_justification_breakdown (Positive) IF enabled
    # 3. _query_justification_breakdown (Negative) IF enabled

    # We expect 1 query only.
    self.assertEqual(self.mock_bq_client.query.call_count, 1)

    # Verify the result contains empty justification breakdown
    youtube_results = results.youtube_video
    self.assertIsNotNone(youtube_results)
    self.assertIsNotNone(youtube_results.justification_breakdown)
    self.assertEqual(youtube_results.justification_breakdown.positive, [])
    self.assertEqual(youtube_results.justification_breakdown.negative, [])

  def test_get_analysis_results_includes_justifications_when_flag_is_true(self):
    # Setup
    dataset = report_msg.SentimentReportDataset(
        dataset_uri="bq://project/dataset/table",
        source=msg_common.SocialMediaSource.YOUTUBE_VIDEO,
        data_output=msg_common.SentimentDataType.SENTIMENT_SCORE
    )

    # Mock BQ responses
    self.mock_bq_client.query.side_effect = [
        # 1. Sentiment Score Query
        [
            {
                "published_week": "2023-01-01",
                "POSITIVE_VIEWS": 100,
                "NEGATIVE_VIEWS": 10,
                "NEUTRAL_VIEWS": 5,
                "TOTAL_VIEWS": 115
            }
        ],
        # 2. Positive Justifications
        [
            {"category": "Price", "sum_of_views": 50}
        ],
        # 3. Negative Justifications
        [
            {"category": "Quality", "sum_of_views": 5}
        ]
    ]

    # Act
    results = self.repo.get_analysis_results(
        [dataset],
        include_justifications=True
    )

    # Assert
    # We expect 3 queries.
    self.assertEqual(self.mock_bq_client.query.call_count, 3)

    youtube_results = results.youtube_video
    self.assertIsNotNone(youtube_results)
    self.assertEqual(len(youtube_results.justification_breakdown.positive), 1)
    self.assertEqual(len(youtube_results.justification_breakdown.negative), 1)

  def test_get_analysis_results_share_of_voice(self):
    """Tests that get_analysis_results handles SHARE_OF_VOICE correctly."""
    # Setup
    dataset = report_msg.SentimentReportDataset(
        dataset_uri="bq://project/dataset/table",
        source=msg_common.SocialMediaSource.YOUTUBE_VIDEO,
        data_output=msg_common.SentimentDataType.SHARE_OF_VOICE
    )

    # Mock BQ response for Share of Voice
    # The query returns rows with "name", "positive", "neutral", "negative"
    # columns. The BigQueryClient wrapper returns a list directly, so we mock
    # return_value (not result())
    self.mock_bq_client.query.return_value = [
        {
            "productOrBrand": "Brand A",
            "Positive_Views": 10,
            "Neutral_Views": 5,
            "Negative_Views": 2
        }
    ]

    # Act
    results = self.repo.get_analysis_results(
        [dataset],
        include_justifications=False
    )

    # Assert
    # Verify ONLY the SOV query was made (excluding justification queries)
    self.assertEqual(self.mock_bq_client.query.call_count, 1)

    youtube_results = results.youtube_video
    self.assertIsNotNone(youtube_results)
    self.assertIsNotNone(youtube_results.share_of_voice)
    self.assertEqual(len(youtube_results.share_of_voice), 1)
    self.assertEqual(youtube_results.share_of_voice[0].name, "Brand A")


if __name__ == "__main__":
  unittest.main()
