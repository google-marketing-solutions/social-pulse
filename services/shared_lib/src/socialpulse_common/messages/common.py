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
"""Module for common types used by all messages."""

import enum


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
