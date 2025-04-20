
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
import logging
from typing import Any
import pandas as pd
from socialpulse_common import config
from socialpulse_common import service
from tasks import core as tasks_core
from tasks.ports import apis as ports_apis

settings = config.Settings()


def _normalize_video_search_results(
    videos_raw: list[dict[str, Any]]
    ) -> pd.DataFrame:
  """Helper Function: Normalizes raw YouTube search results and selects/renames columns.

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
  )[
      [
          "id.videoId",
          "videoUrl",
          "snippet.title",
          "snippet.description",
          "snippet.channelId",
          "snippet.channelTitle",
          "snippet.publishedAt",
      ]
  ].rename(
      columns={
          "id.videoId": "videoId",
          "snippet.title": "videoTitle",
          "snippet.description": "videoDescription",
          "snippet.channelId": "channelId",
          "snippet.channelTitle": "channelTitle",
          "snippet.publishedAt": "publishedAt",
      }
  )
  return videos_df


class FindYoutubeVideos(tasks_core.SentimentTask):
  """Luigi Task to find YouTube videos based on criteria in WorkflowExecutionParams.

  Uses the YoutubeApiClient to search the YouTube API for videos
  matching the topic and date range specified in the workflow execution
  parameters. It normalizes the results into a DataFrame and stores them
  using the configured SentimentDataRepo.
  """

  def output(self) -> tasks_core.SentimentDataRepoTarget:
    """Defines the output target for this task using SentimentDataRepoTarget.

    The output is a dataset managed by the SentimentDataRepo, named using
    the task family (FindYoutubeVideos) and execution ID.

    Returns:
      An instance of SentimentDataRepoTarget representing the task's
      output dataset.
    """
    return tasks_core.SentimentDataRepoTarget(self.dataset_name)

  def _build_search_criteria(self) -> ports_apis.YoutubeSearchCriteria:
    """Builds the search criteria object from workflow params and defaults."""

    topic = self.workflow_exec.topic
    language = ports_apis.Language.ENGLISH
    sort_by = ports_apis.VideoResultsSortBy.RELEVANCE
    max_results = 1000

    criteria = ports_apis.YoutubeSearchCriteria(
        query=topic,
        language=language,
        sort_by=sort_by,
        max_results=max_results
    )

    if self.workflow_exec.HasField("start_time"):
      start_date = self.workflow_exec.start_time.ToDatetime().date()
      criteria.published_after = start_date

    if self.workflow_exec.HasField("end_time"):
      end_date = self.workflow_exec.end_time.ToDatetime().date()
      criteria.published_before = end_date

    logging.info(
        "[%s] Constructed search criteria: %s", self.task_family, criteria
    )
    return criteria

  def run(self) -> None:
    """Execute the video finding logic."""
    logging.info(
        "[%s] Starting FindYoutubeVideos task for execution id: %s",
        self.task_family, self.execution_id
    )

    try:
      youtube_client: ports_apis.YoutubeApiClient = service.registry.get(
          ports_apis.YoutubeApiClient
      )

      criteria = self._build_search_criteria()
      logging.info(
          "[%s] Searching YouTube for videos (execution %s)...",
          self.task_family, self.execution_id
      )

      videos_raw = youtube_client.search_for_videos(criteria)

      if not videos_raw:
        logging.error("[%s] No videos found for criteria in execution %s."
                      "Cannot proceed with analysis.",
                      self.task_family,
                      self.execution_id)
        raise ValueError(
            f"[{self.task_family}] No videos found matching criteria for "
            f"execution {self.execution_id}. Analysis cannot continue."
        )

      videos_df = _normalize_video_search_results(videos_raw)
      # Use the specific method from SentimentDataRepoTarget
      self.output().write_sentiment_data(videos_df)
      logging.info(
          "[%s] Successfully wrote video data for execution %s.",
          self.task_family, self.execution_id
      )

    except Exception as e:
      logging.exception(
          "[%s] Task failed during execution %s due to %s: %s",
          self.task_family, self.execution_id, type(e).__name__, e
      )
      raise
