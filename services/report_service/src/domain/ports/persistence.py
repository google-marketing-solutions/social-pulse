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
import dataclasses
import typing

from socialpulse_common import service
from socialpulse_common.messages import common as msg_common
from socialpulse_common.messages import sentiment_report


@dataclasses.dataclass
class SentimentReportSearchFilter:
  """Filter for searching sentiment reports.

  Properties:
    status: The status of the sentiment report to filter by.
  """
  status: msg_common.SentimentReportStatus


class SentimentReportRepo(abc.ABC, service.RegisterableService):
  """Interface for CRUD operations on a sentiment report."""

  @abc.abstractmethod
  def get_report(self, report_id: str):
    """Retrieves a sentiment report by its ID."""
    raise NotImplementedError

  @abc.abstractmethod
  def persist_report(self, report: sentiment_report.SentimentReport):
    """Creates or updates a sentiment report.

    Persists a report, by checking if it already has a UUID.  If not, then it
    will insert the report into persistent storage.  If it does have a UUID,
    it will update the report record in storage.

    Args:
      report: The sentiment report to persist.
    """
    raise NotImplementedError


class SentimentReportSearchRepo(abc.ABC, service.RegisterableService):
  """Interface for searching sentiment reports."""

  @abc.abstractmethod
  def find_reports(
      self,
      filters: typing.List[SentimentReportSearchFilter]
  ) -> typing.List[sentiment_report.SentimentReport]:
    """Retrieves sentiment reports by the provided filters.

    Args:
      filters: A list of filters to apply to the search.
    Returns:
      A list of sentiment reports matching the provided filters.
    """
