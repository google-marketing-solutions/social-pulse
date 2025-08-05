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
"""Module for Sentiment Reports dataclasses and enums."""

import dataclasses
import datetime
import enum
import typing

import common as msg_common


class Status(enum.Enum):
  """Status types of a sentiment report."""
  NEW = 0
  COLLECTING_DATA = 1
  DATA_COLLECTED = 2
  GENERATING_REPORT = 3
  COMPLETED = 4
  FAILED = 5


class ReportArtifactType(enum.Enum):
  """Types of artifacts that can be generated for a sentiment report."""
  BQ_TABLE = 0
  GOOGLE_SHEET = 1


@dataclasses.dataclass
class SentimentReportDataset:
  """Represents the sentiment data sets created to produce a report."""
  report_id: str
  source: msg_common.SocialMediaSource
  data_output: msg_common.SentimentDataType
  dataset_uri: str


@dataclasses.dataclass
class SentimentReport:
  """Represents a specific sentiment report.

  A sentiment report can lead to multiple workflows that need to be executed,
  with each workflow analyzing sentiment of a certain topic, from a
  certain source, within a certain timeframe.
  """
  # Unique identifier for this report.
  report_id: typing.Optional[str] = None

  # Current report status.
  status: typing.Optional[Status] = None

  # Which social media sources to find and analyze
  sources: typing.List[msg_common.SocialMediaSource] = dataclasses.field(
      default_factory=list
  )

  # Types of output data types this report will produce.
  report_data_types: typing.List[
      msg_common.SentimentDataType
  ] = dataclasses.field(default_factory=list)

  # Start and end time of the analysis this execution will perform.
  start_time: typing.Optional[datetime.datetime] = None
  end_time: typing.Optional[datetime.datetime] = None

  # Flag to include justifications when producing sentiment scores.
  include_justifications: typing.Optional[bool] = None

  # Information on the topic the analysis will be performed on.
  topic: typing.Optional[str] = None

  # List of sentiment datasets created for this report
  datasets: typing.List[SentimentReportDataset] = dataclasses.field(
      default_factory=list
  )

  # Info on the final artifact created after all datasets are created.
  report_artifact_type: ReportArtifactType = ReportArtifactType.BQ_TABLE
  report_artifact_uri: typing.Optional[str] = None
