# Copyright 2025 Google LLC
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

import datetime
import unittest
from unittest import mock

from domain import sentiment_report as sre
import parameterized
from socialpulse_common.messages import common as common_msg
from socialpulse_common.messages import sentiment_report as report_msg


class SentimentReportEntityTest(unittest.TestCase):
  """Tests the SentimentReportEntity domain class."""

  def setUp(self):
    super().setUp()
    self.sources = [
        common_msg.SocialMediaSource.YOUTUBE_VIDEO,
        common_msg.SocialMediaSource.X_POST,
    ]
    self.data_output = common_msg.SentimentDataType.SENTIMENT_SCORE
    self.start_date = datetime.datetime(2023, 1, 1)
    self.end_date = datetime.datetime(2023, 1, 31)

    self._setup_now_datetime()

  def _setup_now_datetime(self):
    """Set up the mock for datetime.datetime.now()."""
    self.mock_now_ts = datetime.datetime(2025, 8, 7, 12, 0, 0)
    self.mock_datetime_patcher = mock.patch(
        "domain.sentiment_report.datetime.datetime"
    )

    self.mock_datetime = self.mock_datetime_patcher.start()
    self.mock_datetime.now.return_value = self.mock_now_ts

  def test_mark_as_completed_succeeds_with_all_sources(self):
    """Succeeds when a dataset exists for each source.

    Given a list of datasets that includes one for each source specified
    in the report.
    When `mark_as_completed` is called
    Then the report status is updated to `COMPLETED` and datasets are
    assigned.
    """
    report = sre.SentimentReportEntity.create_sentiment_report(
        topic="Test Topic",
        sources=self.sources,
        data_output=self.data_output,
        start_time=self.start_date,
        end_time=self.end_date,
    )

    datasets = [
        report_msg.SentimentReportDataset(
            report_id=report.entity_id,
            source=self.sources[0],
            dataset_uri="uri_twitter",
            data_output=self.data_output,
        ),
        report_msg.SentimentReportDataset(
            report_id=report.entity_id,
            source=self.sources[1],
            dataset_uri="uri_facebook",
            data_output=self.data_output,
        ),
    ]

    report.mark_as_completed(datasets)

    self.assertEqual(report.status, report_msg.Status.COMPLETED)
    self.assertEqual(report.datasets, datasets)
    self.assertEqual(report.last_updated, self.mock_now_ts)

  def test_mark_as_completed_fails_if_datasets_is_empty(self):
    """Fails when the datasets list is empty.

    Given an empty list of datasets is provided.
    When `mark_as_completed` is called
    Then a `ValueError` is raised.
    """
    report = sre.SentimentReportEntity.create_sentiment_report(
        topic="Test Topic",
        sources=self.sources,
        data_output=self.data_output,
        start_time=self.start_date,
        end_time=self.end_date,
    )

    with self.assertRaisesRegex(ValueError, "Datasets cannot be empty."):
      report.mark_as_completed([])

  def test_mark_as_completed_fails_if_a_source_is_missing_a_dataset(self):
    """Fails when a source is missing a dataset.

    Given a list of datasets that is missing a dataset for one of the
    report"s sources.
    When `mark_as_completed` is called
    Then a `ValueError` is raised.
    """
    report = sre.SentimentReportEntity.create_sentiment_report(
        topic="Test Topic",
        sources=self.sources,
        data_output=self.data_output,
        start_time=self.start_date,
        end_time=self.end_date,
    )

    datasets = [
        report_msg.SentimentReportDataset(
            report_id=report.entity_id,
            source=self.sources[0],
            dataset_uri="uri_twitter",
            data_output=self.data_output,
        )
    ]

    with self.assertRaisesRegex(ValueError, "SocialMediaSource.X_POST"):
      report.mark_as_completed(datasets)

  @parameterized.parameterized.expand(
      [
          (
              "empty_topic",
              "",
              [common_msg.SocialMediaSource.YOUTUBE_VIDEO],
              common_msg.SentimentDataType.SENTIMENT_SCORE,
              "Topic cannot be empty.",
          ),
          (
              "empty_sources",
              "Valid Topic",
              [],
              common_msg.SentimentDataType.SENTIMENT_SCORE,
              "Sources cannot be empty.",
          ),
          (
              "none_data_output",
              "Valid Topic",
              [common_msg.SocialMediaSource.YOUTUBE_VIDEO],
              None,
              "Data output cannot contain an empty output.",
          ),
      ]
  )
  def test_create_sentiment_report_fails_with_invalid_fields(
      self,
      name,
      topic,
      sources,
      data_output,
      expected_message,
  ):
    """Fails when any required field is invalid.

    Given a set of invalid fields
    When the `create_sentiment_report` factory is called for each case
    Then a `ValueError` with a specific message is raised.

    Args:
      name: The name of the test case.
      topic: The topic for the report.
      sources: The social media sources for the report.
      data_output: The data output type for the report.
      expected_message: The expected error message.
    """
    del name
    with self.assertRaisesRegex(ValueError, expected_message):
      sre.SentimentReportEntity.create_sentiment_report(
          topic=topic,
          sources=sources,
          data_output=data_output,
          start_time=self.start_date,
      )

  @parameterized.parameterized.expand(
      [
          (
              "empty_datasets",
              [],
              "Datasets cannot be empty.",
          ),
          (
              "missing_dataset_uri",
              [
                  report_msg.SentimentReportDataset(
                      report_id="some_id",
                      source=common_msg.SocialMediaSource.X_POST,
                      data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
                      dataset_uri="",
                  )
              ],
              "Dataset URI cannot be empty.",
          ),
          (
              "missing_source",
              [
                  report_msg.SentimentReportDataset(
                      report_id="some_id",
                      source=None,
                      data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
                      dataset_uri="gs://bucket/some_data",
                  )
              ],
              "Source cannot be empty.",
          ),
          (
              "missing_data_output",
              [
                  report_msg.SentimentReportDataset(
                      report_id="some_id",
                      source=common_msg.SocialMediaSource.X_POST,
                      data_output=None,
                      dataset_uri="gs://bucket/some_data",
                  )
              ],
              "Data output cannot be empty.",
          ),
          (
              "missing_one_source_dataset",
              [
                  report_msg.SentimentReportDataset(
                      report_id="some_id",
                      source=common_msg.SocialMediaSource.X_POST,
                      data_output=common_msg.SentimentDataType.SENTIMENT_SCORE,
                      dataset_uri="gs://bucket/x_post_data",
                  )
              ],
              r"Missing datasets for the following sources:" +
              r".*SocialMediaSource\.YOUTUBE_VIDEO",
          ),
      ]
  )
  def test_mark_as_completed_fails_with_invalid_datasets(
      self, name, datasets, expected_message
  ):
    """Fails when any dataset validation rule is violated.

    Given a set of invalid datasets
    When `mark_as_completed` is called for each case
    Then a `ValueError` with a specific message is raised.

    Args:
      name: The name of the test case.
      datasets: The list of datasets to test with.
      expected_message: The expected error message.
    """
    del name

    with self.assertRaisesRegex(ValueError, expected_message):
      report = sre.SentimentReportEntity.create_sentiment_report(
          topic="Test Topic",
          sources=self.sources,
          data_output=self.data_output,
          start_time=self.start_date,
          end_time=self.end_date,
      )
      report.mark_as_completed(datasets)
