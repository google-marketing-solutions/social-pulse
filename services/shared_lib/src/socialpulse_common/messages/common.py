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


class SocialMediaSource(enum.StrEnum):
  """Sources of social media content."""
  UNKNOWN = "UNKNOWN"
  YOUTUBE_VIDEO = "YOUTUBE_VIDEO"
  YOUTUBE_COMMENT = "YOUTUBE_COMMENT"
  REDDIT_POST = "REDDIT_POST"
  X_POST = "X_POST"
  APP_STORE_REVIEW = "APP_STORE_REVIEW"


class TopicType(enum.StrEnum):
  """Types of topics, affecting any prompts generated downstream."""
  UNKNOWN = "UNKNOWN"
  BRAND_OR_PRODUCT = "BRAND_OR_PRODUCT"
  NON_BRAND = "NON_BRAND"


class SentimentDataType(enum.StrEnum):
  """Types of sentiment data an analysis can produce."""
  UNKNOWN = "UNKNOWN"
  SENTIMENT_SCORE = "SENTIMENT_SCORE"
  SHARE_OF_VOICE = "SHARE_OF_VOICE"
