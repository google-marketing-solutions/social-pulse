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
  start_time: datetime.datetime
  end_time: datetime.datetime
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
      start_time: datetime.datetime,
      include_justifications: bool = False,
      end_time: datetime.datetime | None = None
  ) -> "SentimentReportEntity":
    """Factory for creating a SentimentReportEntity.

    Args:
      topic: The topic of the report.
      sources: The sources of the report.
      data_output: The data output of the report.
      start_time: The start of the date range of the report.
      include_justifications: Whether to include justifications in the report.
      end_time: The end of the date range of the report.

    Returns:
      A new SentimentReportEntity.
    """
    if end_time is None:
      end_time = datetime.datetime.now()

    report = SentimentReportEntity(
        topic=topic,
        status=report_msg.Status.NEW,
        sources=sources,
        data_outputs=[data_output],
        include_justifications=include_justifications,
        start_time=start_time,
        end_time=end_time,
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
      data_outputs: list[common_msg.SentimentDataType] | None = None,
      include_justifications: bool | None = None,
      start_time: datetime.datetime | None = None,
      end_time: datetime.datetime | None = None,
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
      start_time: The start of the date range for the report's analysis.
      end_time: The end of the date range for the report's analysis.
      datasets: A list of sentiment datasets associated with the report.
    """
    super().__init__(
        entity_id=report_id,
        created=created,
        last_updated=last_updated,
    )

    self._topic = topic
    self._status = status
    self._sources = sources
    self._data_outputs = data_outputs
    self._include_justifications = include_justifications
    self._start_time = start_time
    self._end_time = end_time
    self._datasets = datasets

    self._validate_fields()

  def _validate_fields(self):
    """Validates the fields of the entity."""
    if not self._topic:
      raise ValueError("Topic cannot be empty.")
    if not self._sources:
      raise ValueError("Sources cannot be empty.")
    if not self._data_outputs:
      raise ValueError("Data output cannot be empty.")
    if not all(data_output for data_output in self._data_outputs):
      raise ValueError("Data output cannot contain an empty output.")

  @property
  def topic(self) -> str:
    """The topic of the report."""
    return self._topic

  @property
  def status(self) -> report_msg.Status:
    """The current status of the report."""
    return self._status

  @property
  def sources(self) -> list[common_msg.SocialMediaSource]:
    """The social media sources included in the report."""
    return self._sources

  @property
  def data_outputs(self) -> list[common_msg.SentimentDataType]:
    """The types of data outputs produced by the report."""
    return self._data_outputs

  @property
  def include_justifications(self) -> bool:
    """Whether justifications are included in the report."""
    return self._include_justifications

  @property
  def start_time(self) -> datetime.datetime:
    """The start of the date range for the report's analysis."""
    return self._start_time

  @property
  def end_time(self) -> datetime.datetime:
    """The end of the date range for the report's analysis."""
    return self._end_time

  @property
  def datasets(self) -> list[report_msg.SentimentReportDataset]:
    """A list of sentiment datasets associated with the report."""
    return self._datasets

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
    self._validate_datasets(datasets)

    self._status = report_msg.Status.COMPLETED
    self._last_updated = datetime.datetime.now()
    self._datasets = datasets

  def _validate_datasets(
      self,
      datasets: list[report_msg.SentimentReportDataset]
  ):
    """Validates the datasets for the report.

    Args:
      datasets: The datasets for the report.
    """
    if not datasets:
      raise ValueError("Datasets cannot be empty.")

    for dataset in datasets:
      if not dataset.dataset_uri:
        raise ValueError("Dataset URI cannot be empty.")
      if not dataset.source:
        raise ValueError("Source cannot be empty.")
      if not dataset.data_output:
        raise ValueError("Data output cannot be empty.")

    dataset_sources = [dataset.source for dataset in datasets]
    all_sources_have_datasets = all(
        source in dataset_sources for source in self.sources
    )
    if not all_sources_have_datasets:
      missing_sources = [
          source for source in self.sources if source not in dataset_sources
      ]
      raise ValueError(
          f"Missing datasets for the following sources: {missing_sources}"
      )
