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
"""Module for report persistence service interfaces/abstract classes."""

import abc
import enum
import typing

from domain import sentiment_report
from socialpulse_common.messages import report_insight as insight_msg
from socialpulse_common.messages import sentiment_report as report_msg


class SentimentReportRepo(abc.ABC):
  """Interface for CRUD operations on a sentiment report."""

  @abc.abstractmethod
  def load_report(
      self, report_id: str
  ) -> sentiment_report.SentimentReportEntity:
    """Retrieves a sentiment report by its ID."""
    raise NotImplementedError

  @abc.abstractmethod
  def persist_report(self, report: sentiment_report.SentimentReportEntity):
    """Creates or updates a sentiment report.

    Persists a report, by checking if it already has a UUID.  If not, then it
    will insert the report into persistent storage.  If it does have a UUID,
    it will update the report record in storage.

    Args:
      report: The sentiment report to persist.
    """
    raise NotImplementedError


class SentimentReportsSortBy(enum.StrEnum):
  """Enum of sentiment report columns to sort by."""
  STATUS = "status"
  TOPIC = "topic"
  START_DATE = "start_date"
  END_DATE = "end_date"
  CREATED_ON = "created_on"


class SentimentReportSearchCriteria:
  """Criteria for filtering/sorting sentiment reports.

  Properties:
    status: The status of the sentiment report to filter by.
    topic: The topic of the sentiment report to filter by.
  """
  def __init__(
       self,
      status: report_msg.Status = None,
      topic_contains: str = "",
      sort_by: SentimentReportsSortBy = SentimentReportsSortBy.CREATED_ON,
      sort_ascending: bool = True
  ):
    self.status = status
    self.topic_contains = topic_contains
    self.sort_by = sort_by
    self.sort_ascending = sort_ascending


class SentimentReportSearchRepo(abc.ABC):
  """Interface for searching sentiment reports."""

  @abc.abstractmethod
  def get_reports(
      self,
      criteria: SentimentReportSearchCriteria
  ) -> typing.List[report_msg.SentimentReport]:
    """Retrieves sentiment reports by the provided filters.

    Args:
      criteria: Criteria by which to filter/sort the results.
    Returns:
      A list of sentiment reports matching the provided criteria.
    """
    raise NotImplementedError


class ReportInsightsRepo(abc.ABC):
  """Interface for CRUD operations on report insights."""

  @abc.abstractmethod
  def insert_insight(
      self,
      report_id: str,
      insight_type: insight_msg.InsightType,
      content: typing.Dict[str, typing.Any],
      raw_prompt_output: str | None = None,
  ):
    """Inserts a new insight for a report."""
    raise NotImplementedError
