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
from socialpulse_common.persistence import bigquery_client


class BigQueryDatasetRepoTest(unittest.TestCase):
  """Tests for BigQueryDatasetRepo."""

  def setUp(self):
    super().setUp()

    self.mock_bq_client = mock.Mock(spec=bigquery_client.BigQueryClient)
    self.repo = bq_dataset_repo.BigQueryDatasetRepo(self.mock_bq_client)

  def test_query_sentiment_breakdown_for_videos(self):
    """Tests the sentiment breakdown query for videos.

    Given a mocked BigQuery client.
    When query_sentiment_breakdown_for_videos is called.
    Then the query is executed and the mocked results are returned.
    """
    self.mock_bq_client.query.return_value = [
        {"published_week": "2023-01-01", "POSITIVE_VIEWS": 100}
    ]
    results = self.repo.query_sentiment_breakdown_for_videos(
        "project.dataset.table"
    )
    self.assertEqual(self.mock_bq_client.query.call_count, 1)
    self.assertEqual(len(results), 1)

  def test_query_sentiment_breakdown_for_comments(self):
    """Tests the sentiment breakdown query for comments.

    Given a mocked BigQuery client.
    When query_sentiment_breakdown_for_comments is called.
    Then the query is executed and the mocked results are returned.
    """
    self.mock_bq_client.query.return_value = [
        {"published_week": "2023-01-01", "POSITIVE_COUNT": 10}
    ]
    results = self.repo.query_sentiment_breakdown_for_comments(
        "project.dataset.table"
    )
    self.assertEqual(self.mock_bq_client.query.call_count, 1)
    self.assertEqual(len(results), 1)

  def test_query_sentiment_breakdown_for_comments_with_filters(self):
    """Tests the sentiment breakdown query for comments with filters.

    Given a mocked BigQuery client.
    When query_sentiment_breakdown_for_comments is called.
    Then the query is executed with the expected WHERE clauses.
    """
    self.mock_bq_client.query.return_value = []
    self.repo.query_sentiment_breakdown_for_comments(
        "project.dataset.table",
        start_date="2023-01-01",
        end_date="2023-12-31",
        channel_title="Test Channel",
        excluded_channels=["Bad Channel 1", "Bad Channel's 2"],
    )

    self.assertEqual(self.mock_bq_client.query.call_count, 1)
    called_query = self.mock_bq_client.query.call_args[0][0]
    self.assertIn("comments.publishedAt >= '2023-01-01'", called_query)
    self.assertIn("comments.publishedAt <= '2023-12-31'", called_query)
    self.assertIn("comments.channelTitle = 'Test Channel'", called_query)
    self.assertIn(
        "comments.channelTitle NOT IN ('Bad Channel 1', 'Bad Channel\\'s 2')",
        called_query,
    )

  def test_query_sentiment_score_summary_for_videos(self):
    """Tests the sentiment score summary query for videos.

    Given a mocked BigQuery client.
    When query_sentiment_score_summary_for_videos is called.
    Then the query is executed and the mocked results are returned.
    """
    self.mock_bq_client.query.return_value = [{
        "POSITIVE_VIEWS": 100,
        "NEGATIVE_VIEWS": 50,
        "NEUTRAL_VIEWS": 25,
        "TOTAL_VIEWS": 175,
        "TOTAL_ITEMS": 10,
    }]
    results = self.repo.query_sentiment_score_summary_for_videos(
        "project.dataset.table"
    )
    self.assertEqual(self.mock_bq_client.query.call_count, 1)
    self.assertEqual(len(results), 1)

  def test_query_sentiment_score_summary_for_comments(self):
    """Tests the sentiment score summary query for comments.

    Given a mocked BigQuery client.
    When query_sentiment_score_summary_for_comments is called.
    Then the query is executed and the mocked results are returned.
    """
    self.mock_bq_client.query.return_value = [{
        "POSITIVE_COUNT": 10,
        "NEGATIVE_COUNT": 5,
        "NEUTRAL_COUNT": 2,
        "TOTAL_ITEMS": 17,
    }]
    results = self.repo.query_sentiment_score_summary_for_comments(
        "project.dataset.table"
    )
    self.assertEqual(self.mock_bq_client.query.call_count, 1)
    self.assertEqual(len(results), 1)

  def test_query_share_of_voice(self):
    """Tests the share of voice query.

    Given a mocked BigQuery client.
    When query_share_of_voice is called.
    Then the query is executed and the mocked results are returned.
    """
    self.mock_bq_client.query.return_value = [
        {"productOrBrand": "Brand A", "Positive_Views": 10}
    ]
    results = self.repo.query_share_of_voice("project.dataset.table")
    self.assertEqual(self.mock_bq_client.query.call_count, 1)
    self.assertEqual(len(results), 1)

  def test_query_justification_breakdown_for_videos(self):
    """Tests the justification breakdown query for videos.

    Given a mocked BigQuery client.
    When query_justification_breakdown_for_videos is called.
    Then the query is executed and the mocked results are returned.
    """
    self.mock_bq_client.query.return_value = [
        {"category": "Price", "sum_of_views": 50}
    ]
    results = self.repo.query_justification_breakdown_for_videos(
        "project.dataset.table", "POSITIVE"
    )
    self.assertEqual(self.mock_bq_client.query.call_count, 1)
    self.assertEqual(len(results), 1)

  def test_query_justification_breakdown_for_comments(self):
    """Tests the justification breakdown query for comments.

    Given a mocked BigQuery client.
    When query_justification_breakdown_for_comments is called.
    Then the query is executed and the mocked results are returned.
    """
    self.mock_bq_client.query.return_value = [
        {"category": "Price", "sum_of_comments": 22}
    ]
    results = self.repo.query_justification_breakdown_for_comments(
        "project.dataset.table", "POSITIVE"
    )
    self.assertEqual(self.mock_bq_client.query.call_count, 1)
    self.assertEqual(len(results), 1)


if __name__ == "__main__":
  unittest.main()
