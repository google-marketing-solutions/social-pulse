"""Copyright 2025 Google LLC.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

 https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import dataclasses
import datetime
import enum


class SocialContentSource(enum.Enum):
  VIDEO_CONTENT = "video_content"
  VIDEO_COMMENT = "video_comment"
  X_POST = "x_thread"
  REDDIT_POST = "reddit_post"
  OTHER = "other"


class ReportType(enum.Enum):
  SENTIMENT_SCORE = "sentiment_score"
  SENTIMENT_JUSTIFICATION = "justification"
  SOURCE_COUNT = "source_count"


class TopicType(enum.Enum):
  BRAND = "brand"
  PRODUCT = "product"
  PRODUCT_FEATURE = "product_feature"
  OTHER = "other"


class TimeUnit(enum.Enum):
  DAY = "day"
  WEEK = "week"
  MONTH = "month"


@dataclasses.dataclass
class Topic:
  name: str
  type: TopicType


@dataclasses.dataclass
class AnalysisWindow:
  topics: list[Topic]
  date_range_start: datetime.date
  date_range_end: datetime.date


@dataclasses.dataclass
class ReportParameters:
  sources: list[SocialContentSource]
  analysis_windows: list[AnalysisWindow]

  event_date: datetime.date | None = None
  report_type: ReportType = ReportType.SENTIMENT_SCORE
  segment_timeframe: TimeUnit = TimeUnit.DAY
