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
"""Module for YouTube Comment Analysis Result Builders."""

import logging

from domain import sentiment_report
from domain.analysis_results import core as builder_core
from domain.ports import dataset
from socialpulse_common import service
from socialpulse_common.messages import analysis_result
from socialpulse_common.messages import common as msg_common
from socialpulse_common.messages import sentiment_report as report_msg


logger = logging.getLogger(__name__)


class _BaseYoutubeCommentBuilder(builder_core.ResultDataBuilder):
  """Base builder for YouTube comment result data."""

  def _get_dataset(
      self,
      report_entity: sentiment_report.SentimentReportEntity,
      data_output: msg_common.SentimentDataType,
  ) -> report_msg.SentimentReportDataset | None:
    for d in report_entity.datasets:
      if (
          d.source == msg_common.SocialMediaSource.YOUTUBE_COMMENT
          and d.data_output == data_output
      ):
        return d
    return None

  def _get_table_id(self, uri: str) -> str:
    if uri.startswith("bq://"):
      return uri[5:].replace("/", ".")
    return uri


class YoutubeCommentSentimentTimelineBuilder(_BaseYoutubeCommentBuilder):
  """Builder for YouTube Comment Sentiment Timeline."""

  def build(
      self,
      report_entity: sentiment_report.SentimentReportEntity,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> analysis_result.BaseAnalysisResultSet | None:
    ds = self._get_dataset(
        report_entity, msg_common.SentimentDataType.SENTIMENT_SCORE
    )
    if not ds or not ds.dataset_uri:
      return None

    repo = service.registry.get(dataset.DatasetRepo)
    table_id = self._get_table_id(ds.dataset_uri)

    rows = repo.query_sentiment_breakdown_for_comments(
        table_id,
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
        relevance_threshold=report_entity.relevance_threshold,
    )

    timeline = []
    for row in rows:
      timeline.append(
          analysis_result.SentimentDataPoint(
              date=row.get("published_week", ""),
              positive=int(row.get("POSITIVE_COUNT", 0)),
              negative=int(row.get("NEGATIVE_COUNT", 0)),
              neutral=int(row.get("NEUTRAL_COUNT", 0)),
          )
      )

    return analysis_result.SentimentOverTimeResultSet(
        sentiment_over_time=timeline
    )


class YoutubeCommentOverallSentimentBuilder(_BaseYoutubeCommentBuilder):
  """Builder for YouTube Comment Overall Sentiment."""

  def build(
      self,
      report_entity: sentiment_report.SentimentReportEntity,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> analysis_result.BaseAnalysisResultSet | None:
    ds = self._get_dataset(
        report_entity, msg_common.SentimentDataType.SENTIMENT_SCORE
    )
    if not ds or not ds.dataset_uri:
      return None

    repo = service.registry.get(dataset.DatasetRepo)
    table_id = self._get_table_id(ds.dataset_uri)

    rows = repo.query_sentiment_score_summary_for_comments(
        table_id,
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
        relevance_threshold=report_entity.relevance_threshold,
    )

    overall_pos = sum(int(row.get("POSITIVE_COUNT", 0)) for row in rows)
    overall_neg = sum(int(row.get("NEGATIVE_COUNT", 0)) for row in rows)
    overall_neu = sum(int(row.get("NEUTRAL_COUNT", 0)) for row in rows)
    item_count = sum(int(row.get("TOTAL_ITEMS", 0)) for row in rows)

    return analysis_result.OverallSentimentResultSet(
        overall_sentiment=analysis_result.OverallSentimentDataPoint(
            positive=overall_pos,
            negative=overall_neg,
            neutral=overall_neu,
            item_count=item_count,
        )
    )


class YoutubeCommentJustificationBuilder(_BaseYoutubeCommentBuilder):
  """Builder for YouTube Comment Justification Breakdown."""

  def build(
      self,
      report_entity: sentiment_report.SentimentReportEntity,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> analysis_result.BaseAnalysisResultSet | None:
    if not report_entity.include_justifications:
      return None

    ds = self._get_dataset(
        report_entity, msg_common.SentimentDataType.SENTIMENT_SCORE
    )
    if not ds or not ds.dataset_uri:
      return None

    repo = service.registry.get(dataset.DatasetRepo)
    table_id = self._get_table_id(ds.dataset_uri)

    pos_rows = repo.query_justification_breakdown_for_comments(
        table_id,
        sentiment_filter="POSITIVE",
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
        relevance_threshold=report_entity.relevance_threshold,
    )
    neg_rows = repo.query_justification_breakdown_for_comments(
        table_id,
        sentiment_filter="NEGATIVE",
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
        relevance_threshold=report_entity.relevance_threshold,
    )

    result = {"positive": [], "negative": [], "neutral": []}

    for row in pos_rows:
      category = row.get("category", "Unknown")
      count = int(row.get("sum_of_comments", 0))
      result["positive"].append(
          analysis_result.JustificationCategoryDataPoint(
              category=category,
              count=count,
          )
      )

    for row in neg_rows:
      category = row.get("category", "Unknown")
      count = int(row.get("sum_of_comments", 0))
      result["negative"].append(
          analysis_result.JustificationCategoryDataPoint(
              category=category,
              count=count,
          )
      )

    # Sort results
    result["positive"] = sorted(
        result["positive"], key=lambda x: x.count, reverse=True
    )
    result["negative"] = sorted(
        result["negative"], key=lambda x: x.count, reverse=True
    )
    result["neutral"] = sorted(
        result["neutral"], key=lambda x: x.count, reverse=True
    )

    return analysis_result.JustificationBreakdownResultSet(
        justification_breakdown=analysis_result.JustificationBreakdown(
            positive=result["positive"],
            negative=result["negative"],
            neutral=result["neutral"],
        )
    )


class YoutubeCommentJustificationCategoryMetadataBuilder(
    _BaseYoutubeCommentBuilder
):
  """Builder for YouTube Comment Justification Category Metadata."""

  def build(
      self,
      report_entity: sentiment_report.SentimentReportEntity
  ) -> analysis_result.JustificationCategoryMetadataResultSet:
    if not report_entity.include_justifications:
      return analysis_result.JustificationCategoryMetadataResultSet(
          justification_categories=[]
      )

    ds = self._get_dataset(
        report_entity, msg_common.SentimentDataType.SENTIMENT_SCORE
    )
    if not ds or not ds.dataset_uri:
      return analysis_result.JustificationCategoryMetadataResultSet(
          justification_categories=[]
      )

    repo = service.registry.get(dataset.DatasetRepo)
    # Map SentimentDataset_XXX to GenerateJustificationCategoriesTask_XXX
    dataset_uri = ds.dataset_uri
    if "SentimentDataset_" not in dataset_uri:
      logger.warning("Unexpected dataset URI format: %s", dataset_uri)
      return analysis_result.JustificationCategoryMetadataResultSet(
          justification_categories=[]
      )

    metadata_uri = dataset_uri.replace(
        "SentimentDataset_", "GenerateJustificationCategoriesTask_"
    )
    table_id = self._get_table_id(metadata_uri)

    rows = repo.query_justification_category_metadata(table_id)

    categories = []
    for row in rows:
      categories.append(
          analysis_result.JustificationCategoryMetadataItem(
              category_name=row.get("categoryName", ""),
              definition=row.get("definition", ""),
              classification_type=row.get("classificationType", ""),
              representative_example=row.get("representativeExample", ""),
          )
      )

    return analysis_result.JustificationCategoryMetadataResultSet(
        justification_categories=categories
    )
