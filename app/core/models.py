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
"""Module providing state classes for the web app."""
import datetime
import enum
import typing

import mesop as me
import pydantic


class ContentSource(enum.Enum):
  YOUTUBE_VIDEOS = "Youtube Videos"
  YOUTUBE_COMMENTS = "Youtube Comments"
  REDDIT_POSTS = "Reddit Posts"
  X_THREADS = "X Threads (Tweats)"


class AnalysisType(enum.Enum):
  SENTIMENT_SCORES = "Sentiment Scores"
  SENTIMENT_SHARE_OF_VOICE = "Sentiment Share of Voice"
  SENTIMENT_SCORES_WITH_JUSTIFICATIONS = "Sentiment Scores with Justifications"


class ConsumptionMethod(enum.Enum):
  GOOGLE_SHEET = "Google Sheet"
  BIG_QUERY_TABLE = "Big Query Table"
  AWS_REDSHIFT_TABLE = "AWS Redshift Table"


class ReportStatus(enum.Enum):
  NEW = "New"
  IN_PROGRESS = "In Progress"
  COMPLETED = "Completed"
  FAILED = "Failed"


class AppRoute(enum.StrEnum):
  """Enumeration of available application routes."""
  DASHBOARD = "Dashboard"
  CREATE_REPORT = "Create Report"
  REPORT_DETAIL = "Report Detail"


@me.stateclass
class AppState:
  """Application state class, for tracking current location and report."""
  current_route: AppRoute = AppRoute.DASHBOARD
  logged_in_user_id: str | None = None
  selected_report_id: str | None = None


class ReportConfig(pydantic.BaseModel):
  """Represents the configuration for a sentiment report."""
  user_id: str
  topic: str
  content_sources: typing.List[ContentSource]
  analysis_type: AnalysisType
  start_date: datetime.date
  consumption_method: ConsumptionMethod

  status: ReportStatus = ReportStatus.NEW
  include_justifications: bool = False

  id: typing.Optional[str] = None
  end_date: typing.Optional[datetime.date] = None
  created_at: typing.Optional[datetime.datetime] = None
  completed_at: typing.Optional[datetime.datetime] = None
  report_link: typing.Optional[str] = None
