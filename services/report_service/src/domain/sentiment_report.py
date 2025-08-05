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
"""Module for the sentiment report entities."""

import datetime
import typing

from socialpulse_common import domain
from socialpulse_common.messages import common as common_msg
from socialpulse_common.messages import sentiment_report as report_msg


class SentimentReportEntity(domain.Entity):
  """Represents a sentiment report entity."""

  topic: str
  status: report_msg.Status
  sources: list[common_msg.SocialMediaSource]
  data_outputs: list[common_msg.SentimentDataType]
  include_justifications: bool
  date_range_start: datetime.datetime
  date_range_end: datetime.datetime
  report_artifact_type: report_msg.ReportArtifactType
  report_artifact_uri: str
  datasets: typing.List[report_msg.SentimentReportDataset]

  @classmethod
  def create_sentiment_report(
      cls,
      *,
      topic: str,
      sources: list[common_msg.SocialMediaSource],
      data_output: common_msg.SentimentDataType,
      include_justifications: bool,
      date_range_start: datetime.datetime,
      date_range_end: datetime.datetime | None = None
  ) -> 'SentimentReportEntity':
    """Factory for creating a SentimentReportEntity.

    Args:
      topic: The topic of the report.
      sources: The sources of the report.
      data_output: The data output of the report.
      include_justifications: Whether to include justifications in the report.
      date_range_start: The start of the date range of the report.
      date_range_end: The end of the date range of the report.

    Returns:
      A new SentimentReportEntity.
    """
    if date_range_end is None:
      date_range_end = datetime.datetime.now()

    report = SentimentReportEntity(
        topic=topic,
        status=report_msg.SentimentReportStatus.NEW,
        sources=sources,
        data_outputs=[data_output],
        include_justifications=include_justifications,
        date_range_start=date_range_start,
        date_range_end=date_range_end,
    )
    return report

  def __init__(
      self,
      *,
      report_id: str | None = None,
      created: datetime.datetime | None = None,
      last_updated: datetime.datetime | None = None,
      topic: str | None = None,
      status: report_msg.Status| None = None,
      sources: list[common_msg.SocialMediaSource] | None = None,
      data_outputs: list[str] | None = None,
      include_justifications: bool | None = None,
      date_range_start: datetime.datetime | None = None,
      date_range_end: datetime.datetime | None = None,
      datasets: list[report_msg.SentimentReportDataset] | None = None,
  ):
    """Initializes a complete SentimentReportEntity from the provided values.

    The constructor is not meant to be called directly, instead it's should only
    be used by data access objects, which are trying to reconstitute a entity
    from persistent storage.  SentityReportEntity's should be created in code
    via the class factory function.

    Args:
      report_id: The unique identifier for the report.
      created: The timestamp when the report was created.
      last_updated: The timestamp when the report was last updated.
      topic: The topic of the report.
      status: The current status of the report.
      sources: The social media sources included in the report.
      data_outputs: The types of data outputs produced by the report.
      include_justifications: Whether justifications are included in the report.
      date_range_start: The start of the date range for the report's analysis.
      date_range_end: The end of the date range for the report's analysis.
      datasets: A list of sentiment datasets associated with the report.
    """
    super().__init__(
        entity_id=report_id,
        created=created,
        last_updated=last_updated,
    )

    self.topic = topic
    self.status = status
    self.sources = sources
    self.data_outputs = data_outputs
    self.include_justifications = include_justifications
    self.date_range_start = date_range_start
    self.date_range_end = date_range_end
    self.datasets = datasets

  def mark_as_collecting_data(self):
    """Marks the report as collecting data."""
    self.status = report_msg.Status.COLLECTING_DATA
    self.last_updated = datetime.datetime.now()

  def mark_as_completed(
      self,
      datasets: list[report_msg.SentimentReportDataset]
  ):
    """Marks the report as completed.

    Args:
      datasets: The datasets for the report.
    """
    self.status = report_msg.Status.COMPLETED
    self.last_updated = datetime.datetime.now()
    self.datasets = datasets
