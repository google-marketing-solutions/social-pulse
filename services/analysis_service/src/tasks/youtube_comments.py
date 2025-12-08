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
"""Task to fetch YT comments for videos."""
import logging
from typing import Any
import pandas as pd
from socialpulse_common import service
from tasks import core as tasks_core
from tasks.ports import apis as ports_apis


class FindYoutubeComments(tasks_core.SentimentTask):
  """Luigi Task to find and flatten YouTube comments for videos found previously.

  Requires the output of FindYoutubeVideos. It fetches comments for each
  videoId using the configured YoutubeApiClient, flattens the reply structure,
  and saves the resulting DataFrame using the configured SentimentDataRepo.
  """

  _FINAL_OUTPUT_COLUMNS = [
      "commentId",
      "videoId",
      "authorId",
      "publishedAt",
      "text",
      "likeCount",
      "numOfReplies",
      "parentId",
  ]

  def run(self) -> None:
    """Executes the comment finding and flattening logic."""
    logging.info(
        "[%s] Starting FindYoutubeComments task for execution ID: %s",
        self.task_family,
        self.execution_id,
    )

    try:
      input_target = self.input()
      logging.info(
          "[%s] Loading video data from required task target: %s",
          self.task_family,
          input_target.table_name,
      )
      videos_df = input_target.load_sentiment_data()
      video_ids = videos_df["videoId"].unique().tolist()

      youtube_client: ports_apis.YoutubeApiClient = service.registry.get(
          ports_apis.YoutubeApiClient
      )

      logging.info(
          "[%s] Fetching comments from YouTube API for %d videos...",
          self.task_family,
          len(video_ids),
      )

      raw_comments_data: list[dict[str, Any]] = (
          youtube_client.get_comments_for_videos(video_ids)
      )

      logging.info(
          "[%s] Processing and flattening comments...", self.task_family
      )

      normalized_threads_df = self._normalize_comment_threads(raw_comments_data)
      flattened_comments_df = self._flatten_comment_replies(
          normalized_threads_df
      )
      merged_df = pd.merge(
          flattened_comments_df,
          videos_df[["videoId", "summary"]],
          on="videoId",
          how="left"
      )

      self.output().write_sentiment_data(merged_df)

    except Exception as e:
      logging.exception(
          "[%s] Task failed during execution %s due to %s: %s",
          self.task_family,
          self.execution_id,
          type(e).__name__,
          e,
      )
      raise

  def _normalize_comment_threads(
      self, raw_comments_data: list[dict[str, Any]]
  ) -> pd.DataFrame:
    """Normalizes raw comment thread data, focusing on top-level comments.

    Args:
      raw_comments_data: List of raw comment thread dicts from the API.

    Returns:
      DataFrame where each row is a top-level comment thread.
    """
    if not raw_comments_data:
      return pd.DataFrame()

    try:
      # Normalize, selecting top-level fields and the replies structure
      # pylint: disable=line-too-long
      comments_dataset = (
          pd.json_normalize(raw_comments_data)[
              [
                  "id",
                  "snippet.videoId",
                  "snippet.topLevelComment.snippet.authorChannelId.value",
                  "snippet.topLevelComment.snippet.publishedAt",
                  "snippet.topLevelComment.snippet.textOriginal",
                  "snippet.topLevelComment.snippet.likeCount",
                  "snippet.totalReplyCount",
                  "replies.comments",
              ]
          ]
          .rename(
              columns={
                  "id": "commentId",
                  "snippet.videoId": "videoId",
                  "snippet.topLevelComment.snippet.authorChannelId.value": "authorId",
                  "snippet.topLevelComment.snippet.publishedAt": "publishedAt",
                  "snippet.topLevelComment.snippet.textOriginal": "text",
                  "snippet.topLevelComment.snippet.likeCount": "likeCount",
                  "snippet.totalReplyCount": "numOfReplies",
                  "replies.comments": "replies",
              }
          )
          .fillna(
              {
                  "likeCount": 0,
                  "numOfReplies": 0,
                  "authorId": "Unknown",
                  "text": "",
              }
          )
          .astype(
              {
                  "likeCount": "int64",
                  "numOfReplies": "int64",
              }
          )
      )
      return comments_dataset
    except Exception as e:
      logging.exception("Error during initial comment normalization: %s", e)
      raise

  def _flatten_comment_replies(
      self, comments_dataset: pd.DataFrame
  ) -> pd.DataFrame:
    """Flattens nested replies from a normalized comment thread DataFrame.

    Args:
      comments_dataset: DataFrame with top-level comments and nested 'replies'.

    Returns:
      A DataFrame where each row is either a top-level comment or a reply.
    """

    try:
      logging.debug(
          "[%s] Starting reply flattening process...", self.task_family
      )
      comments_top_level = comments_dataset.copy()
      comments_top_level["parentId"] = pd.NA

      processed_replies_df = self._process_and_normalize_replies(
          comments_top_level
      )

      comments_top_level_final = self._prepare_top_level_for_concat(
          comments_top_level
      )

      flattened_comments_df = self._concatenate_replies(
          comments_top_level_final, processed_replies_df
      )
      final_df = self._finalize_dataframe(flattened_comments_df)
      return final_df

    except Exception as e:
      logging.exception("Error during comment reply flattening: %s", e)
      raise

  def _process_and_normalize_replies(
      self, comments_top_level: pd.DataFrame
  ) -> pd.DataFrame | None:
    """Isolates, explodes, normalizes, and processes reply comments."""

    if "replies" not in comments_top_level.columns:
      logging.warning(
          "[%s] 'replies' column not in input. No replies to process.",
          self.task_family,
      )
      return None

    # pylint: disable=g-explicit-length-test
    has_replies_filter = comments_top_level["replies"].apply(
        lambda x: isinstance(x, list) and len(x) > 0
    )
    comments_with_replies = comments_top_level[has_replies_filter].copy()

    if comments_with_replies.empty:
      logging.debug(
          "[%s] No comment threads contained replies.", self.task_family
      )
      return None

    try:
      replies_exploded = comments_with_replies.explode(
          "replies", ignore_index=True
      )

      try:
        normalized_replies = pd.json_normalize(replies_exploded["replies"])
      except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error(
            "[%s] Error normalizing exploded replies: %s. Skipping replies.",
            self.task_family,
            e,
        )
        return None

      if normalized_replies.empty:
          return None
      processed_replies_filled = pd.DataFrame()
      if not normalized_replies.empty:
        cols_to_select = [
            "id",
            "snippet.authorChannelId.value",
            "snippet.publishedAt",
            "snippet.textOriginal",
            "snippet.likeCount",
        ]
        existing_cols = [
            col for col in cols_to_select if col in normalized_replies.columns
        ]
        processed_replies_renamed = normalized_replies[existing_cols].rename(
            columns={
                "id": "commentId",
                "snippet.authorChannelId.value": "authorId",
                "snippet.publishedAt": "publishedAt",
                "snippet.textOriginal": "text",
                "snippet.likeCount": "likeCount",
            }
        )
        processed_replies_filled = processed_replies_renamed.fillna(
            {"likeCount": 0, "authorId": "Unknown", "text": ""}
        ).astype({"likeCount": "int64"})

        # Derive Parent ID
        processed_replies_filled["parentId"] = (
            processed_replies_filled["commentId"]
            .astype(str)
            .str.partition(".")[0]
        )
        processed_replies_filled["videoId"] = replies_exploded["videoId"].values
        processed_replies_filled["numOfReplies"] = 0
      return processed_replies_filled

    except Exception as e:
      logging.exception(
          "[%s] Unexpected error processing replies: %s", self.task_family, e
      )
      raise

  def _prepare_top_level_for_concat(
      self, comments_top_level: pd.DataFrame
  ) -> pd.DataFrame:
    """Prepares the top-level comments DataFrame for final concatenation."""
    logging.debug(
        "[%s] Preparing top-level comments for concat...", self.task_family
    )
    comments_top_level_final = comments_top_level.drop(
        columns=["replies", "_has_replies"], errors="ignore"
    )

    for col in self._FINAL_OUTPUT_COLUMNS:
      if col not in comments_top_level_final.columns:
        comments_top_level_final[col] = pd.NA
    return comments_top_level_final[self._FINAL_OUTPUT_COLUMNS]

  def _concatenate_replies(
      self,
      comments_top_level_final: pd.DataFrame,
      processed_replies_df: pd.DataFrame | None,
  ) -> pd.DataFrame:
    """Concatenates top-level comments and processed replies."""
    if processed_replies_df is not None and not processed_replies_df.empty:
      logging.debug(
          "[%s] Concatenating %d top-level and %d reply rows...",
          self.task_family,
          len(comments_top_level_final),
          len(processed_replies_df),
      )
      # Ensure reply df has same columns before concat
      for col in self._FINAL_OUTPUT_COLUMNS:
        if col not in processed_replies_df.columns:
          processed_replies_df[col] = pd.NA
      processed_replies_df = processed_replies_df[self._FINAL_OUTPUT_COLUMNS]

      flattened_comments_df = pd.concat(
          [comments_top_level_final, processed_replies_df], ignore_index=True
      )
      return flattened_comments_df
    else:
      logging.debug(
          "[%s] No replies to concatenate, using only top-level.",
          self.task_family,
      )
      return comments_top_level_final

  def _finalize_dataframe(self, flattened_df: pd.DataFrame) -> pd.DataFrame:
    """Performs final fillna and type casting."""
    final_df = flattened_df.fillna({"numOfReplies": 0, "likeCount": 0})
    final_df = final_df[self._FINAL_OUTPUT_COLUMNS].astype(
        {"numOfReplies": "int64", "likeCount": "int64"}
    )
    return final_df
