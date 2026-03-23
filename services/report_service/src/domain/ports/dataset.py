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
"""Module for dataset persistence interface."""

import abc
import typing

from socialpulse_common import service
from socialpulse_common.messages import sentiment_report as report_msg


class DatasetRepo(service.RegisterableService):
  """Interface for retrieving dataset analysis results."""

  @abc.abstractmethod
  def query_share_of_voice(
      self,
      table_id: str,
      start_date: typing.Optional[str] = None,
      end_date: typing.Optional[str] = None,
      channel_title: typing.Optional[str] = None,
      excluded_channels: typing.Optional[typing.List[str]] = None,
      relevance_threshold: int = 90,
  ) -> typing.List[typing.Dict[str, typing.Any]]:
    """Executes query for SHARE_OF_VOICE."""

  @abc.abstractmethod
  def query_share_of_voice_totals(
      self,
      table_id: str,
      start_date: typing.Optional[str] = None,
      end_date: typing.Optional[str] = None,
      channel_title: typing.Optional[str] = None,
      excluded_channels: typing.Optional[typing.List[str]] = None,
      relevance_threshold: int = 90,
  ) -> typing.Dict[str, int]:
    """Queries total item count and views for Share of Voice context."""

  @abc.abstractmethod
  def query_sentiment_breakdown_for_videos(
      self,
      table_id: str,
      start_date: typing.Optional[str] = None,
      end_date: typing.Optional[str] = None,
      channel_title: typing.Optional[str] = None,
      excluded_channels: typing.Optional[typing.List[str]] = None,
      relevance_threshold: int = 90,
  ) -> typing.List[typing.Dict[str, typing.Any]]:
    """Queries for timeseries breakdown of sentiment scores for videos."""

  @abc.abstractmethod
  def query_sentiment_breakdown_for_comments(
      self,
      table_id: str,
      start_date: typing.Optional[str] = None,
      end_date: typing.Optional[str] = None,
      channel_title: typing.Optional[str] = None,
      excluded_channels: typing.Optional[typing.List[str]] = None,
      relevance_threshold: int = 90,
  ) -> typing.List[typing.Dict[str, typing.Any]]:
    """Queries for timeseries breakdown of sentiment scores for comments."""

  @abc.abstractmethod
  def query_sentiment_score_summary_for_videos(
      self,
      table_id: str,
      start_date: typing.Optional[str] = None,
      end_date: typing.Optional[str] = None,
      channel_title: typing.Optional[str] = None,
      excluded_channels: typing.Optional[typing.List[str]] = None,
      relevance_threshold: int = 90,
  ) -> typing.List[typing.Dict[str, typing.Any]]:
    """Queries for summary stats of sentiment scores for videos."""

  @abc.abstractmethod
  def query_sentiment_score_summary_for_comments(
      self,
      table_id: str,
      start_date: typing.Optional[str] = None,
      end_date: typing.Optional[str] = None,
      channel_title: typing.Optional[str] = None,
      excluded_channels: typing.Optional[typing.List[str]] = None,
      relevance_threshold: int = 90,
  ) -> typing.List[typing.Dict[str, typing.Any]]:
    """Queries for summary stats of sentiment scores for comments."""

  @abc.abstractmethod
  def query_justification_breakdown_for_videos(
      self,
      table_id: str,
      sentiment_filter: str,
      start_date: typing.Optional[str] = None,
      end_date: typing.Optional[str] = None,
      channel_title: typing.Optional[str] = None,
      excluded_channels: typing.Optional[typing.List[str]] = None,
  ) -> typing.List[typing.Dict[str, typing.Any]]:
    """Executes query for Justification Breakdown."""

  @abc.abstractmethod
  def query_justification_breakdown_for_comments(
      self,
      table_id: str,
      sentiment_filter: str,
      start_date: typing.Optional[str] = None,
      end_date: typing.Optional[str] = None,
      channel_title: typing.Optional[str] = None,
      excluded_channels: typing.Optional[typing.List[str]] = None,
  ) -> typing.List[typing.Dict[str, typing.Any]]:
    """Executes query for Justification Breakdown for comments."""

  @abc.abstractmethod
  def query_justification_category_metadata(
      self,
      table_id: str,
  ) -> typing.List[typing.Dict[str, typing.Any]]:
    """Queries justification category metadata.

    Args:
      table_id: Table ID in project.dataset.table format.

    Returns:
      List of dictionaries containing the category metadata.
    """

  @abc.abstractmethod
  def get_channels(
      self,
      datasets: typing.List[report_msg.SentimentReportDataset],
      query: typing.Optional[str] = None,
  ) -> typing.List[str]:
    """Retrieves a list of unique channels for the provided datasets.

    Args:
      datasets: List of datasets to retrieve channels for.
      query: Optional query to filter channels by.

    Returns:
      List of unique channel names.
    """
    raise NotImplementedError
