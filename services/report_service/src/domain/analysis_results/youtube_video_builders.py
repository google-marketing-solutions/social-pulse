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
"""Module for YouTube Video Analysis Result Builders."""

import logging
import typing

from domain import sentiment_report
from domain.analysis_results import core as builder_core
from domain.ports import dataset
from socialpulse_common import service

from socialpulse_common.messages import analysis_result
from socialpulse_common.messages import common as msg_common
from socialpulse_common.messages import sentiment_report as report_msg


logger = logging.getLogger(__name__)


class _BaseYoutubeVideoBuilder(builder_core.ResultDataBuilder):
  """Base builder for YouTube video result data."""

  def _get_dataset(
      self,
      report_entity: sentiment_report.SentimentReportEntity,
      data_output: msg_common.SentimentDataType,
  ) -> report_msg.SentimentReportDataset | None:
    for d in report_entity.datasets:
      if (
          d.source == msg_common.SocialMediaSource.YOUTUBE_VIDEO
          and d.data_output == data_output
      ):
        return d
    return None

  def _get_table_id(self, uri: str) -> str:
    if uri.startswith("bq://"):
      return uri[5:].replace("/", ".")
    return uri


class YoutubeVideoSentimentTimelineBuilder(_BaseYoutubeVideoBuilder):
  """Builder for YouTube Video Sentiment Timeline."""

  def build(
      self,
      report_entity: sentiment_report.SentimentReportEntity,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> analysis_result.SentimentOverTimeResultSet:
    ds = self._get_dataset(
        report_entity, msg_common.SentimentDataType.SENTIMENT_SCORE
    )
    if not ds or not ds.dataset_uri:
      return analysis_result.SentimentOverTimeResultSet(sentiment_over_time=[])

    repo = service.registry.get(dataset.DatasetRepo)
    table_id = self._get_table_id(ds.dataset_uri)

    rows = repo.query_sentiment_breakdown_for_videos(
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
              positive=int(row.get("POSITIVE_VIEWS", 0)),
              negative=int(row.get("NEGATIVE_VIEWS", 0)),
              neutral=int(row.get("NEUTRAL_VIEWS", 0)),
          )
      )

    return analysis_result.SentimentOverTimeResultSet(
        sentiment_over_time=timeline
    )


class YoutubeVideoOverallSentimentBuilder(_BaseYoutubeVideoBuilder):
  """Builder for YouTube Video Overall Sentiment."""

  def build(
      self,
      report_entity: sentiment_report.SentimentReportEntity,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> analysis_result.OverallSentimentResultSet:
    ds = self._get_dataset(
        report_entity, msg_common.SentimentDataType.SENTIMENT_SCORE
    )
    if not ds or not ds.dataset_uri:
      return analysis_result.OverallSentimentResultSet(
          overall_sentiment=analysis_result.OverallSentimentDataPoint(
              positive=0, negative=0, neutral=0, average=0.0, item_count=0
          )
      )

    repo = service.registry.get(dataset.DatasetRepo)
    table_id = self._get_table_id(ds.dataset_uri)

    rows = repo.query_sentiment_score_summary_for_videos(
        table_id,
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
        relevance_threshold=report_entity.relevance_threshold,
    )

    overall_pos = sum(int(row.get("POSITIVE_VIEWS", 0)) for row in rows)
    overall_neg = sum(int(row.get("NEGATIVE_VIEWS", 0)) for row in rows)
    overall_neu = sum(int(row.get("NEUTRAL_VIEWS", 0)) for row in rows)
    item_count = sum(int(row.get("TOTAL_ITEMS", 0)) for row in rows)

    return analysis_result.OverallSentimentResultSet(
        overall_sentiment=analysis_result.OverallSentimentDataPoint(
            positive=overall_pos,
            negative=overall_neg,
            neutral=overall_neu,
            item_count=item_count,
        )
    )


class YoutubeVideoJustificationBuilder(_BaseYoutubeVideoBuilder):
  """Builder for YouTube Video Justification Breakdown."""

  def build(
      self,
      report_entity: sentiment_report.SentimentReportEntity,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> analysis_result.JustificationBreakdownResultSet:
    if not report_entity.include_justifications:
      return analysis_result.JustificationBreakdownResultSet(
          justification_breakdown=analysis_result.JustificationBreakdown(
              positive=[], negative=[], neutral=[]
          )
      )

    ds = self._get_dataset(
        report_entity, report_entity.data_outputs[0]
    )
    if not ds or not ds.dataset_uri:
      return analysis_result.JustificationBreakdownResultSet(
          justification_breakdown=analysis_result.JustificationBreakdown(
              positive=[], negative=[], neutral=[]
          )
      )

    repo = service.registry.get(dataset.DatasetRepo)
    table_id = self._get_table_id(ds.dataset_uri)

    pos_rows = repo.query_justification_breakdown_for_videos(
        table_id,
        sentiment_filter="POSITIVE",
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
    )
    neg_rows = repo.query_justification_breakdown_for_videos(
        table_id,
        sentiment_filter="NEGATIVE",
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
    )

    result = {"positive": [], "negative": [], "neutral": []}

    for row in pos_rows:
      category = row.get("category", "Unknown")
      count = int(row.get("sum_of_views", 0))
      result["positive"].append(
          analysis_result.JustificationCategoryDataPoint(
              category=category,
              count=count,
          )
      )

    for row in neg_rows:
      category = row.get("category", "Unknown")
      count = int(row.get("sum_of_views", 0))
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


class YoutubeVideoJustificationCategoryMetadataBuilder(
    _BaseYoutubeVideoBuilder
):
  """Builder for YouTube Video Justification Category Metadata."""

  def build(
      self,
      report_entity: sentiment_report.SentimentReportEntity,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> analysis_result.JustificationCategoryMetadataResultSet:
    if not report_entity.include_justifications:
      return analysis_result.JustificationCategoryMetadataResultSet(
          justification_categories=[]
      )

    ds = self._get_dataset(
        report_entity, report_entity.data_outputs[0]
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


class YoutubeVideoShareOfVoiceBuilder(_BaseYoutubeVideoBuilder):
  """Builder for YouTube Video Share of Voice."""

  def build(
      self,
      report_entity: sentiment_report.SentimentReportEntity,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> analysis_result.ShareOfVoiceResultSet | None:
    ds = self._get_dataset(
        report_entity, msg_common.SentimentDataType.SHARE_OF_VOICE
    )
    if not ds or not ds.dataset_uri:
      return None

    repo = service.registry.get(dataset.DatasetRepo)
    table_id = self._get_table_id(ds.dataset_uri)

    rows = repo.query_share_of_voice(
        table_id,
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
        relevance_threshold=report_entity.relevance_threshold,
    )

    sov_items = []
    for row in rows:
      sov_items.append(
          analysis_result.ShareOfVoiceDataPoint(
              name=row.get("productOrBrand", "Unknown"),
              positive=int(row.get("Positive_Views", 0)),
              negative=int(row.get("Negative_Views", 0)),
              neutral=int(row.get("Neutral_Views", 0)),
          )
      )

    return analysis_result.ShareOfVoiceResultSet(share_of_voice=sov_items)


class YoutubeVideoShareOfVoiceStatsBuilder(_BaseYoutubeVideoBuilder):
  """Builder for YouTube Video Share of Voice Stats."""

  def build(
      self,
      report_entity: sentiment_report.SentimentReportEntity,
      start_date: typing.Optional[str] = None,
      end_date: typing.Optional[str] = None,
      channel_title: typing.Optional[str] = None,
      excluded_channels: typing.Optional[typing.List[str]] = None,
  ) -> analysis_result.OverallSentimentResultSet:
    ds = self._get_dataset(
        report_entity, msg_common.SentimentDataType.SHARE_OF_VOICE
    )
    if not ds or not ds.dataset_uri:
      return analysis_result.OverallSentimentResultSet(
          overall_sentiment=analysis_result.OverallSentimentDataPoint(
              positive=0, negative=0, neutral=0, average=0.0, item_count=0
          )
      )

    repo = service.registry.get(dataset.DatasetRepo)
    table_id = self._get_table_id(ds.dataset_uri)

    totals = repo.query_share_of_voice_totals(
        table_id,
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
        relevance_threshold=report_entity.relevance_threshold,
    )

    overall_pos = totals.get("positive", 0)
    overall_neg = totals.get("negative", 0)
    overall_neu = totals.get("neutral", 0)
    item_count = totals.get("item_count", 0)

    total = overall_pos + overall_neg + overall_neu
    average = 0.0
    if total > 0:
      average = (overall_pos - overall_neg) / total

    return analysis_result.OverallSentimentResultSet(
        overall_sentiment=analysis_result.OverallSentimentDataPoint(
            positive=overall_pos,
            negative=overall_neg,
            neutral=overall_neu,
            average=average,
            item_count=item_count,
        )
    )
