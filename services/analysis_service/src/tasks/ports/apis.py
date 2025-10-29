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

"""Module for external API client interfaces (Ports)."""

import abc
import dataclasses
import datetime
import enum
import pprint
from typing import Any

from socialpulse_common import service


class VideoResultsSortBy(enum.Enum):
  RELEVANCE = "relevance"
  UPLOAD_DATE = "date"
  VIEW_COUNT = "viewCount"
  RATING = "rating"
  TITLE = "title"


class Language(enum.Enum):
  ENGLISH = "en"
  SPANISH = "es"
  FRENCH = "fr"
  GERMAN = "de"


@dataclasses.dataclass
class YoutubeSearchCriteria:
  """Represents the criteria for searching videos on YouTube."""
  query: str
  language: Language = Language.ENGLISH
  sort_by: VideoResultsSortBy = VideoResultsSortBy.RELEVANCE
  max_results: int = 1000
  published_after: datetime.date | None = None
  published_before: datetime.date | None = None

  def published_after_as_str(self) -> str | None:
    """Formats published_after date for YouTube API."""
    if self.published_after is None:
      return None
    return self.published_after.strftime("%Y-%m-%dT23:59:59Z")

  def published_before_as_str(self) -> str | None:
    """Formats published_before date for YouTube API."""
    if self.published_before is None:
      return None
    return self.published_before.strftime("%Y-%m-%dT00:00:00Z")

  def __str__(self):
    """String representation for logging."""
    return pprint.pformat(self.__dict__)


class YoutubeApiClient(service.RegisterableService, abc.ABC):
  """Abstract interface for interacting with the YouTube Data API."""

  @abc.abstractmethod
  def search_for_videos(
      self, criteria: YoutubeSearchCriteria
  ) -> list[dict[str, Any]]:
    """Searches for videos based on the given criteria.

    Args:
      criteria: The search criteria object.

    Returns:
      A list of raw video item dictionaries as returned by the YouTube API.
      Returns an empty list if no videos are found. Implementations should
      handle pagination internally to meet criteria.max_results.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def get_video_details(
      self, video_ids: list[str]
  ) -> dict[str, dict[str, Any]]:
    """Retrieves detailed information for video IDs.

    Args:
      video_ids: A list of YouTube video IDs.

    Returns:
       dict of video stats keyed to their video ID.  The key is a string with
       video ID, and the value is another dict of stat keyed to their values.
       Implementations should handle batching requests based on API limits.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def get_comments_for_videos(
      self, video_ids: list[str]
  ) -> list[dict[str, Any]]:
    """Retrieves comment threads for videos.

    Args:
      video_ids: A list of YouTube video IDs.

    Returns:
      A list of raw comment thread item dictionaries as returned by the API.
      Returns an empty list if no comments are found. Implementations should
      handle iterating through video IDs and comment pagination.
    """
    raise NotImplementedError


class LlmBatchJobApiClient(abc.ABC):
  """Abstract interface for interacting with the LLM Batch Job API."""

  @abc.abstractmethod
  def submit_batch_job(
      self, input_table_name: str, output_table_name: str
  ) -> None:
    """Submit a batch prediction job to the LLM.

    This function will package and submit the batch analysis job, waiting
    for the job to complete with either a success (returns), or raises an
    error on a failure.

    Args:
      input_table_name: The URI of the input table where requests will be read
        from.
      output_table_name: The URI of the output table where responses will be
        written to.
    """
    raise NotImplementedError
