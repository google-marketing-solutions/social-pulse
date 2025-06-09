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

"""Module providing concrete implementation for YoutubeApiClient using googleapiclient."""


import logging
from typing import Any

from googleapiclient import discovery
from googleapiclient import errors

from tasks.ports import apis as ports_apis
logger = logging.getLogger(__name__)

_DEFAULT_API_SERVICE_NAME = "youtube"
_DEFAULT_API_VERSION = "v3"
_MAX_VIDEO_IDS_PER_SEARCH_RESPONSE = 50
_MAX_VIDEO_IDS_PER_DETAIL_REQUEST = 50
_MAX_VIDEO_IDS_PER_COMMENTS_REQUEST = 100


class YoutubeApiHttpClient(ports_apis.YoutubeApiClient):
  """Implementation of YoutubeApiClient using googleapiclient.

  Handles interactions with the YouTube Data API v3 using the discovery client.
  Manages API key authentication, pagination, and basic error handling.
  """

  def __init__(
      self,
      api_key: str,
      service_name: str = _DEFAULT_API_SERVICE_NAME,
      version: str = _DEFAULT_API_VERSION
  ):
    """Initializes the YoutubeApiHttpClient.

    Args:
      api_key (str): The YouTube Data API key.
      service_name (str): The name of the YouTube Data API service.
      version (str): The version of the YouTube Data API.
    """
    if not api_key:
      logger.error("YouTube API key is required.")
      raise ValueError("API key is required for YoutubeApiHttpClient.")

    try:
      self._client = discovery.build(
          service_name,
          version,
          developerKey=api_key,
      )
      logger.info(
          "YT API client built successfully (service=%s, version=%s).",
          service_name, version
      )
    except errors.HttpError as e:
      logger.exception(
          "HTTP error building YouTube API client (is API enabled?): %s", e
      )
      raise
    except Exception as _:
      logger.exception("Failed to build YouTube API client.")
      raise

  def search_for_videos(
      self, criteria: ports_apis.YoutubeSearchCriteria
  ) -> list[dict[str, Any]]:

    """Searches for videos using the YouTube Data API based on the given criteria.

    Args:
        criteria (YoutubeSearchCriteria): The search criteria for finding
        videos.

    Returns:
        list: A list of video items, where each item is a dictionary
        containing video details.
    """

    num_videos_collected = 0
    video_items: list[dict[str, Any]] = []
    next_page_token: str | None = None

    logger.info("Searching YouTube with criteria: %s", criteria)

    while num_videos_collected < criteria.max_results:
      num_of_results = min(
          [_MAX_VIDEO_IDS_PER_SEARCH_RESPONSE,
           criteria.max_results - num_videos_collected]
      )

      try:
        # Prepare request parameters, excluding None values
        request_params = {
            "part": "snippet",
            "type": "video",
            "maxResults": num_of_results,
            "order": criteria.sort_by.value,
            "q": criteria.query,
            "relevanceLanguage": criteria.language.value,
            "pageToken": next_page_token,
            "publishedAfter": criteria.published_after_as_str(),
            "publishedBefore": criteria.published_before_as_str(),
        }
        # Filter out None values before making the call
        request_params = {
            k: v for k, v in request_params.items() if v is not None
        }

        request = self._client.search().list(**request_params)
        response = request.execute()

        found_items = response.get("items", [])
        video_items.extend(found_items)
        count_this_page = len(found_items)
        num_videos_collected += count_this_page

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
          break

      except errors.HttpError as e:
        logger.error(
            "HTTP error %s during YT search page fetch: %s", e.resp.status, e
        )
        raise
      except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error during YouTube search pagination.")
        raise

    logger.info(
        "YouTube search finished. Collected %d video items.",
        num_videos_collected
    )
    return video_items

  def get_video_details(self, video_ids: list[str]) -> list[dict[str, Any]]:
    """Retrieves detailed information for a list of video IDs.

    Args:
        video_ids (list[str]): A list of YouTube video IDs.

    Returns:
        list: A list of video items containing detailed information.

    """
    if not video_ids:
      logger.warning("get_video_details called with empty video_ids list.")
      return []

    # Remove duplicates to avoid unnecessary API calls
    total_ids = len(video_ids)
    current_window_start_index = 0
    current_window_end_index = 0
    video_items: list[dict[str, Any]] = []

    while current_window_start_index < total_ids:
      # Calculate end index for slicing, respecting API limits
      current_window_end_index = min(
          current_window_start_index + _MAX_VIDEO_IDS_PER_DETAIL_REQUEST,
          total_ids
      )

      video_ids_slice = video_ids[
          current_window_start_index : current_window_end_index
      ]

      logger.debug(
          "Getting details for videos index %d to %d",
          current_window_start_index, current_window_end_index
      )

      try:
        request = self._client.videos().list(
            part="statistics",
            id=",".join(video_ids_slice),
            maxResults=_MAX_VIDEO_IDS_PER_DETAIL_REQUEST
        )
        response = request.execute()
        found_items = response.get("items", [])
        video_items.extend(found_items)
        logger.debug(
            "Fetched details for %d videos in this batch.", len(found_items)
        )
      except errors.HttpError as e:
        logger.error(
            "HTTP error %s getting video details for batch"
            "starting at index %d: %s",
            e.resp.status, current_window_start_index, e
        )
        raise
      except Exception:
        logger.exception(
            "Error getting video details for batch starting at index %d.",
            current_window_start_index
        )
        raise
      # Move to the next batch start index
      current_window_start_index += _MAX_VIDEO_IDS_PER_DETAIL_REQUEST

    logger.info(
        "Finished fetching details. Retrieved details for %d videos.",
        len(video_items)
    )
    return video_items

  def get_comments_for_videos(self,
                              video_ids: list[str]) -> list[dict[str, Any]]:
    """Retrieves comments for multiple videos by iterating calls to a helper."""
    if not video_ids:
      return []

    # Remove duplicates
    all_comments: list[dict[str, Any]] = []
    total_videos = len(video_ids)
    logger.info("Fetching comments for %d videos...", total_videos)

    for video_id in video_ids:
      # Call helper method for single video pagination
      video_comments = self._get_comments_for_single_video(video_id)
      all_comments.extend(video_comments)

    logger.info(
        "Finished fetching comments. Retrieved %d comment threads total.",
        len(all_comments)
    )
    return all_comments

  def _get_comments_for_single_video(self,
                                     video_id: str) -> list[dict[str, Any]]:
    """Helper to retrieve all comment threads for a specific video.

    Args:
        video_id (str): The ID of the YouTube video.

    Returns:
        list: A list of comment items for the specified video.
    """
    video_comments: list[dict[str, Any]] = []
    next_page_token: str | None = None
    page_num = 0

    while True:
      page_num += 1
      logger.debug("Fetching comments page %d for video %s", page_num, video_id)
      try:
        request = self._client.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page_token
        )

        response = request.execute()
        found_items = response.get("items", [])
        video_comments.extend(found_items)

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
          logger.debug("No more comment pages for video %s.", video_id)
          break

      except errors.HttpError as e:
        logger.error(
            "HTTP error %s getting comments for video %s: %s",
            e.resp.status, video_id, e
        )
        return []

      except Exception:  # pylint: disable=broad-exception-caught
        logger.exception(
            "Unexpected error getting comments page %d for video %s.",
            page_num, video_id
        )
        return []

    return video_comments


