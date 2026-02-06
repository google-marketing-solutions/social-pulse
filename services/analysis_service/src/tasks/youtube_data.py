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

"""Task to fetch YT data."""
import datetime
import logging

from typing import Any
import pandas as pd
from socialpulse_common import service
from tasks import core as tasks_core
from tasks.ports import apis as ports_apis

# Max results per month when we shard the search by month
MAX_RESULTS_PER_MONTH_SHARD = 50


class FindYoutubeVideos(tasks_core.SentimentTask):
  """Luigi Task to find YouTube videos required by the workflow execution.

  Uses the YoutubeApiClient to search the YouTube API for videos
  matching the topic and date range specified in the workflow execution
  parameters. It normalizes the results into a DataFrame and stores them
  using the configured SentimentDataRepo.
  """

  def _generate_monthly_intervals(
      self, start_date: datetime.date, end_date: datetime.date
  ) -> list[tuple[datetime.date, datetime.date]]:
    """Generates a list of start/end date tuples for monthly intervals."""
    intervals = []
    current_start = start_date
    while current_start < end_date:
      # Use pandas for easy month addition, preserving day or capping at month
      # end
      next_month = current_start + pd.DateOffset(months=1)
      current_end = next_month.date()

      # If the step goes past the global end_date, cap it
      if current_end > end_date:
        current_end = end_date

      intervals.append((current_start, current_end))
      current_start = current_end

    return intervals

  def _build_search_criteria(
      self,
      max_results: int = 500
  ) -> ports_apis.YoutubeSearchCriteria:
    """Builds the search criteria object from workflow params and defaults."""
    topic = self.workflow_exec.topic
    sort_by = ports_apis.VideoResultsSortBy.RELEVANCE

    criteria = ports_apis.YoutubeSearchCriteria(
        query=topic, sort_by=sort_by, max_results=max_results
    )

    logging.info(
        "[%s] Constructed base search criteria: %s", self.task_family, criteria
    )
    return criteria

  def _normalize_video_search_results(
      self, videos_raw: list[dict[str, Any]]
  ) -> pd.DataFrame:
    """Normalize raw YouTube search results and selects/renames columns.

    Args:
      videos_raw: A list of raw video item dictionaries from the YouTube API
    search.list endpoint.

    Returns:
      A pandas DataFrame containing processed video data with columns:
      videoId, videoUrl, videoTitle, videoDescription, channelId,
      channelTitle, publishedAt.
    """

    yt_data_api_response_items_df = pd.json_normalize(videos_raw)
    videos_df = yt_data_api_response_items_df.assign(
        videoUrl="http://www.youtube.com/watch?v="
        + yt_data_api_response_items_df["id.videoId"]
    )[[
        "id.videoId",
        "videoUrl",
        "snippet.title",
        "snippet.description",
        "snippet.channelId",
        "snippet.channelTitle",
        "snippet.publishedAt",
    ]].rename(
        columns={
            "id.videoId": "videoId",
            "snippet.title": "videoTitle",
            "snippet.description": "videoDescription",
            "snippet.channelId": "channelId",
            "snippet.channelTitle": "channelTitle",
            "snippet.publishedAt": "publishedAt",
        }
    )

    videos_df = videos_df.drop_duplicates(subset=["videoId"])
    return videos_df

  def _attach_video_stats_to_video_data(
      self, video_df: pd.DataFrame
  ) -> pd.DataFrame:
    """Attaches meta data about the videos to the video data."""
    youtube_client: ports_apis.YoutubeApiClient = service.registry.get(
        ports_apis.YoutubeApiClient
    )

    video_id_list = video_df["videoId"].tolist()
    video_stats_lookup = youtube_client.get_video_details(video_id_list)

    stats_series = video_df["videoId"].map(video_stats_lookup)
    valid_stats_list = stats_series.dropna().tolist()

    if not valid_stats_list:
      logging.warning("No video statistics found for any of the video IDs.")
      return video_df

    stats_df = pd.json_normalize(valid_stats_list)
    stats_df = stats_df.rename(
        columns={
            "id": "videoId",  # Rename 'id' to 'videoId' for merging
            "statistics.viewCount": "viewCount",
            "statistics.likeCount": "likeCount",
            "statistics.commentCount": "commentCount",
            "statistics.favoriteCount": "favoriteCount",
        }
    )

    columns_to_keep = [
        "videoId",
        "viewCount",
        "likeCount",
        "commentCount",
        "favoriteCount",
    ]
    final_stats_df = stats_df[[
        col for col in columns_to_keep if col in stats_df.columns
    ]]
    merged_df = pd.merge(video_df, final_stats_df, on="videoId", how="left")

    numeric_cols = [
        "viewCount",
        "likeCount",
        "commentCount",
        "favoriteCount",
    ]
    merged_df[numeric_cols] = merged_df[numeric_cols].apply(
        pd.to_numeric, errors="coerce"
    )

    return merged_df

  def run(self) -> None:
    """Execute the video finding logic."""
    logging.info(
        "[%s] Starting FindYoutubeVideos task for execution id: %s",
        self.task_family,
        self.execution_id,
    )

    try:
      youtube_client: ports_apis.YoutubeApiClient = service.registry.get(
          ports_apis.YoutubeApiClient
      )

      videos_raw = []

      # If no date range is specified, fallback to a single search
      if not self.workflow_exec.start_time or not self.workflow_exec.end_time:
        logging.warning(
            "[%s] No date range specified. Using simple search.",
            self.task_family
        )
        criteria = self._build_search_criteria()
        videos_raw = youtube_client.search_for_videos(criteria)

      else:
        # Shard the search by month
        intervals = self._generate_monthly_intervals(
            self.workflow_exec.start_time.date(),
            self.workflow_exec.end_time.date()
        )
        logging.info(
            "[%s] Sharding search into %d intervals for execution %s.",
            self.task_family,
            len(intervals),
            self.execution_id,
        )

        for start_date, end_date in intervals:
          criteria = self._build_search_criteria(
              max_results=MAX_RESULTS_PER_MONTH_SHARD
          )
          criteria.published_after = start_date
          criteria.published_before = end_date

          logging.info(
              "[%s] Searching interval %s to %s...", self.task_family,
              start_date, end_date
          )

          interval_videos = youtube_client.search_for_videos(criteria)
          videos_raw.extend(interval_videos)

      logging.info(
          "[%s] Found %s total videos matching criteria for execution %s.",
          self.task_family,
          len(videos_raw),
          self.execution_id,
      )

      if not videos_raw:
        logging.error(
            "[%s] No videos found for criteria in execution %s."
            "Cannot proceed with analysis.",
            self.task_family,
            self.execution_id,
        )
        raise ValueError(
            f"[{self.task_family}] No videos found matching criteria for "
            f"execution {self.execution_id}. Analysis cannot continue."
        )

      videos_df = self._normalize_video_search_results(videos_raw)
      videos_df = self._attach_video_stats_to_video_data(videos_df)

      self.output().write_sentiment_data(videos_df)

      logging.info(
          "[%s] Successfully wrote video data for execution %s.",
          self.task_family,
          self.execution_id,
      )

    except Exception as e:
      logging.exception(
          "[%s] Task failed during execution %s due to %s: %s",
          self.task_family,
          self.execution_id,
          type(e).__name__,
          e,
      )
      raise
