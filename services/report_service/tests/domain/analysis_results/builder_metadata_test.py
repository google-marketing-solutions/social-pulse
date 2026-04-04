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
"""Unit tests for the Justification Category Metadata Builders."""

import unittest
from unittest import mock

from domain import sentiment_report
from domain.analysis_results import youtube_comment_builders
from domain.analysis_results import youtube_video_builders
from domain.ports import dataset
from socialpulse_common import service
from socialpulse_common.messages import common as msg_common
from socialpulse_common.messages import sentiment_report as report_msg


class JustificationCategoryMetadataBuilderTest(unittest.TestCase):
  """Tests for JustificationCategoryMetadata builders."""

  def setUp(self):
    super().setUp()
    self.mock_repo = mock.Mock(spec=dataset.DatasetRepo)
    service.registry.register(dataset.DatasetRepo, self.mock_repo)

    self.report_entity = mock.create_autospec(
        sentiment_report.SentimentReportEntity, instance=True
    )
    self.report_entity.include_justifications = True

  def test_youtube_video_metadata_builder(self):
    """Tests the video metadata builder.

    Given a report with a video dataset and mocked repository.
    When build is called.
    Then the repository is queried with the correctly resolved table ID.
    """
    ds = report_msg.SentimentReportDataset(
        report_id="123",
        source=msg_common.SocialMediaSource.YOUTUBE_VIDEO,
        data_output=msg_common.SentimentDataType.SENTIMENT_SCORE,
        dataset_uri="bq://project/dataset/SentimentDataset_XXX",
    )
    self.report_entity.datasets = [ds]
    self.mock_repo.query_justification_category_metadata.return_value = [
        {"categoryName": "Cat 1", "definition": "Def 1"}
    ]

    builder = (
        youtube_video_builders.YoutubeVideoJustificationCategoryMetadataBuilder()
    )
    result = builder.build(self.report_entity)

    self.assertEqual(len(result.justification_categories), 1)
    self.assertEqual(result.justification_categories[0].category_name, "Cat 1")
    self.mock_repo.query_justification_category_metadata.assert_called_once_with(
        "project.dataset.GenerateJustificationCategoriesTask_XXX"
    )

  def test_youtube_comment_metadata_builder(self):
    """Tests the comment metadata builder.

    Given a report with a comment dataset and mocked repository.
    When build is called.
    Then the repository is queried with the correctly resolved table ID.
    """
    ds = report_msg.SentimentReportDataset(
        report_id="123",
        source=msg_common.SocialMediaSource.YOUTUBE_COMMENT,
        data_output=msg_common.SentimentDataType.SENTIMENT_SCORE,
        dataset_uri="bq://project/dataset/SentimentDataset_YYY",
    )
    self.report_entity.datasets = [ds]
    self.mock_repo.query_justification_category_metadata.return_value = [
        {"categoryName": "Cat 2", "definition": "Def 2"}
    ]

    builder = (
        youtube_comment_builders.YoutubeCommentJustificationCategoryMetadataBuilder()
    )
    result = builder.build(self.report_entity)

    self.assertEqual(len(result.justification_categories), 1)
    self.assertEqual(result.justification_categories[0].category_name, "Cat 2")
    self.mock_repo.query_justification_category_metadata.assert_called_once_with(
        "project.dataset.GenerateJustificationCategoriesTask_YYY"
    )


if __name__ == "__main__":
  unittest.main()
