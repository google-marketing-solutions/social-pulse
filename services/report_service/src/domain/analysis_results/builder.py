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
"""Module for Analysis Results Builders."""

import logging
import typing

from domain import sentiment_report
from domain.analysis_results import core as builder_core
from domain.analysis_results import youtube_comment_builders
from domain.analysis_results import youtube_video_builders
from socialpulse_common.messages import analysis_result
from socialpulse_common.messages import common as common_msg
from socialpulse_common.messages import sentiment_report as report_msg


logger = logging.getLogger(__name__)

# List of builders for Youtube video sentiment timeline.
_YT_VIDEO_TIMELINE_BUILDERS = [
    youtube_video_builders.YoutubeVideoSentimentTimelineBuilder(),
    youtube_video_builders.YoutubeVideoOverallSentimentBuilder(),
    youtube_video_builders.YoutubeVideoJustificationBuilder(),
]

# List of builders for Youtube video share of voice.
_YT_VIDEO_SHARE_OF_VOICE_BUILDERS = [
    youtube_video_builders.YoutubeVideoShareOfVoiceBuilder(),
    youtube_video_builders.YoutubeVideoShareOfVoiceStatsBuilder(),
]

# List of builders for Youtube comment sentiment analysis.
_YT_COMMENT_BUILDERS = [
    youtube_comment_builders.YoutubeCommentSentimentTimelineBuilder(),
    youtube_comment_builders.YoutubeCommentOverallSentimentBuilder(),
    youtube_comment_builders.YoutubeCommentJustificationBuilder(),
]

# The _deep_merge function has been removed as we are now populating
# strong fields directly onto SourceAnalysisResult objects.


class CompositeAnalysisResultsBuilder:
  """Composite builder that aggregates results from registered builders."""

  def build_results(
      self,
      report_entity: sentiment_report.SentimentReportEntity,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> dict[str, typing.Any]:
    """Runs all registered builders and aggregates their results.

    Args:
      report_entity: The sentiment report entity.
      start_date: Optional start date filter.
      end_date: Optional end date filter.
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.

    Returns:
      Dictionary mapping SocialMediaSource string to SourceAnalysisResult.
    """
    results: dict[str, analysis_result.SourceAnalysisResult] = {}

    if not getattr(report_entity, "datasets", None):
      return results

    for dataset in report_entity.datasets:
      builders = self._get_builders_for_dataset(dataset)
      source_key = dataset.source.value

      if source_key not in results:
        results[source_key] = analysis_result.SourceAnalysisResult()

      source_result = results[source_key]

      for builder in builders:
        try:
          partial_result = builder.build(
              report_entity,
              start_date=start_date,
              end_date=end_date,
              channel_title=channel_title,
              excluded_channels=excluded_channels,
          )

          if partial_result:
            if isinstance(
                partial_result, analysis_result.SentimentOverTimeResultSet
            ):
              source_result.sentiment_over_time = (
                  partial_result.sentiment_over_time
              )
            elif isinstance(
                partial_result, analysis_result.OverallSentimentResultSet
            ):
              source_result.overall_sentiment = partial_result.overall_sentiment
            elif isinstance(
                partial_result,
                analysis_result.JustificationBreakdownResultSet,
            ):
              source_result.justification_breakdown = (
                  partial_result.justification_breakdown
              )
            elif isinstance(
                partial_result, analysis_result.ShareOfVoiceResultSet
            ):
              source_result.share_of_voice = partial_result.share_of_voice

        except Exception as e:  # pylint: disable=broad-exception-caught
          logger.warning("Builder %s failed: %s", type(builder).__name__, e)

    # Return exactly model_dump by alias so it's JSON serializable camelCase
    # directly!
    return {
        k: v.model_dump(by_alias=True, exclude_none=True)
        for k, v in results.items()
    }

  def _get_builders_for_dataset(
      self, dataset: report_msg.SentimentReportDataset
  ) -> list[builder_core.ResultDataBuilder]:
    """Get builders for a specific dataset type.

    Note: This function will return an empty list if no builders are registered
    for the given dataset source and output type.

    Args:
      dataset: Report dataset.

    Returns:
      List of builders for the given dataset type.
    """
    if dataset.source == common_msg.SocialMediaSource.YOUTUBE_VIDEO:
      if dataset.data_output == common_msg.SentimentDataType.SENTIMENT_SCORE:
        return _YT_VIDEO_TIMELINE_BUILDERS
      else:
        return _YT_VIDEO_SHARE_OF_VOICE_BUILDERS

    elif dataset.source == common_msg.SocialMediaSource.YOUTUBE_COMMENT:
      return _YT_COMMENT_BUILDERS

    logger.warning("No builders found for dataset: %s", dataset)
    return []
