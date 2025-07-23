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
"""Module for Workflow Execution dataclasses and enums."""
import dataclasses
import datetime
import enum
import typing


class SocialMediaSource(enum.Enum):
  """Sources of social media content."""
  UNKNOWN = 0
  YOUTUBE_VIDEO = 1
  YOUTUBE_COMMENT = 2
  REDDIT_POST = 3
  X_POST = 4
  APP_STORE_REVIEW = 5


class TopicType(enum.Enum):
  """Types of topics, affecting any prompts generated downstream."""
  UNKNOWN = 0
  BRAND_OR_PRODUCT = 1
  NON_BRAND = 2


class SentimentDataType(enum.Enum):
  """Types of sentiment data an analysis can produce."""
  UNKNOWN = 0
  SENTIMENT_SCORE = 1
  SHARE_OF_VOICE = 2


class Status(enum.Enum):
  """Status types of a workflow execution."""
  UNKNOWN = 0
  NEW = 1
  IN_PROGRESS = 2
  COMPLETED = 3
  FAILED = 4


@dataclasses.dataclass
class WorkflowExecutionParams:
  """Represents a specific execution of a sentiment workflow.

  A sentiment report can lead to multiple workflows that need to be executed,
  with each workflow analyzing sentiment of a certain topic, from a
  certain source, within a certain timeframe. This message represents a
  specific execution of that workflow.
  """
  # Unique identifier for this execution.
  execution_id: typing.Optional[str] = None

  # Source of the social media content.
  source: typing.Optional[SocialMediaSource] = None

  # Type of sentiment data that should be produced by this execution.
  data_output: typing.List[SentimentDataType] = dataclasses.field(
      default_factory=list
  )

  # Information on the topic the analysis will be performed on.
  topic_type: typing.Optional[TopicType] = None
  topic: typing.Optional[str] = None

  # Start and end time of the analysis this execution will perform.
  start_time: typing.Optional[datetime] = None
  end_time: typing.Optional[datetime] = None

  # The last completed task.
  last_completed_task_id: typing.Optional[str] = None

  # Current workflow status.
  status: typing.Optional[Status] = None

  # Flag to include justifications when producing sentiment scores.
  include_justifications: typing.Optional[bool] = None

  # ID of a parent workflow exec this one depends on.
  parent_execution_id: typing.Optional[str] = None
