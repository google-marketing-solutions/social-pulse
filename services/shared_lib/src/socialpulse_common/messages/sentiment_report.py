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

import datetime
import enum
import typing

import pydantic
from pydantic import alias_generators
import socialpulse_common.messages.common as msg_common


class Status(enum.StrEnum):
  """Status types of a sentiment report."""
  NEW = "NEW"
  COLLECTING_DATA = "COLLECTING_DATA"
  DATA_COLLECTED = "DATA_COLLECTED"
  GENERATING_REPORT = "GENERATING_REPORT"
  COMPLETED = "COMPLETED"
  FAILED = "FAILED"


class ReportArtifactType(enum.StrEnum):
  """Types of artifacts that can be generated for a sentiment report."""
  BQ_TABLE = "BQ_TABLE"
  GOOGLE_SHEET = "GOOGLE_SHEET"


class SentimentReportDataset(pydantic.BaseModel):
  """Represents the sentiment data sets created to produce a report."""
  model_config = pydantic.ConfigDict(
      use_enum_names=True,
      populate_by_name=True,
      alias_generator=alias_generators.to_camel,
  )

  report_id: typing.Optional[str] = None
  source: typing.Optional[msg_common.SocialMediaSource] = None
  data_output: typing.Optional[msg_common.SentimentDataType] = None
  dataset_uri: typing.Optional[str] = None


class SentimentReport(pydantic.BaseModel):
  """Represents a specific sentiment report.

  A sentiment report can lead to multiple workflows that need to be executed,
  with each workflow analyzing sentiment of a certain topic, from a
  certain source, within a certain timeframe.
  """
  model_config = pydantic.ConfigDict(
      use_enum_names=True,
      populate_by_name=True,
      alias_generator=alias_generators.to_camel,
  )

  # Unique identifier for this report.
  report_id: typing.Optional[str] = None

  # Timestamp of when this report was created
  created_on: typing.Optional[datetime.datetime] = None

  # Timestamp of when this report was last updated
  last_updated_on: typing.Optional[datetime.datetime] = None

  # Current report status.
  status: typing.Optional[Status] = None

  # Which social media sources to find and analyze
  sources: list[msg_common.SocialMediaSource] = (
      pydantic.Field(default_factory=list)
  )

  # The type of data output for this report
  data_output: msg_common.SentimentDataType = None

  # Start and end time of the analysis this execution will perform.
  start_time: typing.Optional[datetime.datetime] = None
  end_time: typing.Optional[datetime.datetime] = None

  # Flag to include justifications when producing sentiment scores.
  include_justifications: typing.Optional[bool] = None

  # Information on the topic the analysis will be performed on.
  topic: typing.Optional[str] = None

  # List of sentiment datasets created for this report
  datasets: list[SentimentReportDataset] = pydantic.Field(default_factory=list)

  # Info on the final artifact created after all datasets are created.
  report_artifact_type: ReportArtifactType = ReportArtifactType.BQ_TABLE
  report_artifact_uri: typing.Optional[str] = None

  # The actual analysis results, if available.
  analysis_results: typing.Optional["AnalysisResults"] = None



class SentimentOverTime(pydantic.BaseModel):
  """Represents sentiment scores over time."""
  model_config = pydantic.ConfigDict(
      use_enum_names=True,
      populate_by_name=True,
      alias_generator=alias_generators.to_camel,
  )
  date: str
  positive: int
  negative: int
  neutral: int


class OverallSentiment(pydantic.BaseModel):
  """Represents overall sentiment statistics."""
  model_config = pydantic.ConfigDict(
      use_enum_names=True,
      populate_by_name=True,
      alias_generator=alias_generators.to_camel,
  )
  positive: int
  negative: int
  neutral: int
  average: float
  item_count: int = 0


class ShareOfVoiceItem(pydantic.BaseModel):
  """Represents a single item in share of voice analysis."""
  model_config = pydantic.ConfigDict(
      use_enum_names=True,
      populate_by_name=True,
      alias_generator=alias_generators.to_camel,
  )
  name: str
  positive: int
  negative: int
  neutral: int


class JustificationItem(pydantic.BaseModel):
  """Represents a single justification category count."""
  model_config = pydantic.ConfigDict(
      use_enum_names=True,
      populate_by_name=True,
      alias_generator=alias_generators.to_camel,
  )
  category: str
  count: int


class JustificationBreakdown(pydantic.BaseModel):
  """Represents a breakdown of justifications by sentiment."""
  model_config = pydantic.ConfigDict(
      use_enum_names=True,
      populate_by_name=True,
      alias_generator=alias_generators.to_camel,
  )
  positive: list[JustificationItem] = pydantic.Field(default_factory=list)
  negative: list[JustificationItem] = pydantic.Field(default_factory=list)
  neutral: list[JustificationItem] = pydantic.Field(default_factory=list)


class SourceAnalysisResult(pydantic.BaseModel):
  """Analysis results for a specific source."""
  model_config = pydantic.ConfigDict(
      use_enum_names=True,
      populate_by_name=True,
      alias_generator=alias_generators.to_camel,
  )
  # For SENTIMENT_SCORE
  sentiment_over_time: typing.Optional[list[SentimentOverTime]] = None
  overall_sentiment: typing.Optional[OverallSentiment] = None
  # For SHARE_OF_VOICE
  share_of_voice: typing.Optional[list[ShareOfVoiceItem]] = None
  # For Justification Breakdown
  justification_breakdown: typing.Optional[JustificationBreakdown] = None


class AnalysisResults(pydantic.BaseModel):
  """Wrapper for analysis results for multiple sources."""
  model_config = pydantic.ConfigDict(
      use_enum_names=True,
      populate_by_name=True,
      alias_generator=alias_generators.to_camel,
  )

  youtube_video: typing.Optional[SourceAnalysisResult] = pydantic.Field(
      default=None, alias="YOUTUBE_VIDEO"
  )
  youtube_comment: typing.Optional[SourceAnalysisResult] = pydantic.Field(
      default=None, alias="YOUTUBE_COMMENT"
  )
  reddit_post: typing.Optional[SourceAnalysisResult] = pydantic.Field(
      default=None, alias="REDDIT_POST"
  )
  x_post: typing.Optional[SourceAnalysisResult] = pydantic.Field(
      default=None, alias="X_POST"
  )
  app_store_review: typing.Optional[SourceAnalysisResult] = pydantic.Field(
      default=None, alias="APP_STORE_REVIEW"
  )


