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
"""Script for performing sentiment analysis on YouTube videos and comments."""
import datetime
import enum
import pprint
import time

from google.cloud import bigquery
from googleapiclient import discovery
from googleapiclient import errors
import pandas as pd
from pipeline.scoring import comment
from pipeline.scoring import video
from socialpulse_common.messages import workflow_execution_pb2 as wfe

import vertexai
from vertexai.batch_prediction import BatchPredictionJob


####### Report dependant variables ################################

######### Use cached video data (saves on YT API calls)
USE_CACHED_VIDEO_DATA = False
USE_CACHED_COMMENT_DATA = False


######### Flags for which analysis to do
PERFORM_VIDEO_ANALYSIS = True
PERFORM_COMMENT_ANALYSIS = False


######### Customer doing analysis for
CUSTOMER = "adobe"


######### Adobe Photoshop for iPhone
# RELEASE_DATE = datetime.date(2025, 2, 25)
# TOPIC = "Photoshop on iPhone"
# REPORT_TABLE_NAME_PREFIX = f"{CUSTOMER}_photoshop"

# ####### Adobe Firefly:  text to video
RELEASE_DATE = datetime.date(2025, 2, 12)
TOPIC = "Adobe Firely Text to Video"
REPORT_TABLE_NAME_PREFIX = (
    f"{CUSTOMER}_firefly_text_to_video"
)


######### GCP Parameters - Fill these out with your project
PROJECT_ID = ""
API_KEY = ""
DATASET_ID = f"social_pulse_{CUSTOMER}"
LOCATION = "us-central1"


API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
YT_SCOPE = ["https://www.googleapis.com/auth/youtube.force-ssl"]


DEFAULT_TOTAL_VIDEOS = 50
MAX_VIDEO_IDS_PER_SEARCH_RESPONSE = 50
MAX_VIDEO_IDS_PER_DETAIL_REQUEST = 50
MAX_VIDEO_IDS_PER_COMMENTS_REQUEST = 20

GEMINI_PRO_MODEL_ID = "gemini-2.0-flash-001"


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


class YoutubeSearchCriteria:
  """Represents the criteria for searching videos on YouTube."""
  query: str
  language: Language
  sort_by: VideoResultsSortBy
  published_after: datetime.date
  published_before: datetime.date
  max_results: int

  def __init__(self, query: str) -> None:
    """Initializes a YoutubeSearchCriteria object.

    Args:
        query (str): The search query string.
    """
    self.query = query
    self.language = Language.ENGLISH
    self.sort_by = VideoResultsSortBy.RELEVANCE
    self.max_results = DEFAULT_TOTAL_VIDEOS
    self.published_after = datetime.date.today()
    self.published_before = self.published_after

  def with_language(self, language: Language):
    self.language = language
    return self

  def with_sort_by(self, sort_by: VideoResultsSortBy):
    self.sort_by = sort_by
    return self

  def with_published_after(self, published_after: datetime.date):
    self.published_after = published_after
    return self

  def with_published_before(self, published_before: datetime.date):
    self.published_before = published_before
    return self

  def with_max_results(self, max_results: int):
    self.max_results = max_results
    return self

  def published_after_as_str(self):
    return self.published_after.strftime("%Y-%m-%dT23:59:59Z")

  def published_before_as_str(self):
    if self.published_before is None:
      return ""
    return self.published_before.strftime("%Y-%m-%dT00:00:00Z")

  def __str__(self):
    return pprint.pformat(self.__dict__)


class YoutubeSearch:
  """A class for searching videos on YouTube using the YouTube Data API."""

  def __init__(self, api_key):
    """Initializes the YoutubeSearch object with the API key.

    Args:
        api_key (str): The YouTube Data API key.
    """
    self._api_key = api_key
    self._client = discovery.build(
        API_SERVICE_NAME,
        API_VERSION,
        developerKey=self._api_key
    )

  def search_for_videos(self, criteria: YoutubeSearchCriteria):
    """Searches for videos on YouTube based on the given criteria.

    Args:
        criteria (YoutubeSearchCriteria): The search criteria for finding
        videos.

    Returns:
        list: A list of video items, where each item is a dictionary
        containing video details.

    """

    num_videos_collected = 0
    video_items = []
    next_page_token = ""

    while num_videos_collected < criteria.max_results:
      num_of_results = min(
          [MAX_VIDEO_IDS_PER_SEARCH_RESPONSE,
           criteria.max_results - num_videos_collected]
      )

      request = self._client.search().list(
          part="snippet",
          type="video",
          maxResults=num_of_results,
          order=criteria.sort_by.value,
          publishedAfter=criteria.published_after_as_str(),
          publishedBefore=criteria.published_before_as_str(),
          q=criteria.query,
          relevanceLanguage=criteria.language.value,
          pageToken=next_page_token
      )

      response = request.execute()
      for item in response["items"]:
        video_items.append(item)
        num_videos_collected += 1

      if "nextPageToken" in response:
        next_page_token = response["nextPageToken"]
      else:
        break

    return video_items

  def get_video_details(self, video_ids: list[str]):
    """Retrieves detailed information for a list of video IDs.

    Args:
        video_ids (list[str]): A list of YouTube video IDs.

    Returns:
        list: A list of video items containing detailed information.

    """
    current_window_start_index = 0
    current_window_end_index = 0
    video_items = []

    print(f"Grabbing details for {len(video_ids)} videos...")
    # pylint: disable=g-explicit-length-test
    while current_window_start_index < len(video_ids):
      current_window_end_index = (
          current_window_start_index + MAX_VIDEO_IDS_PER_DETAIL_REQUEST - 1)

      print(
          f"...getting details for videos {current_window_start_index}"
          f"to {current_window_end_index}"
      )
      video_ids_slice = video_ids[
          current_window_start_index : current_window_end_index]

      request = self._client.videos().list(
          part="statistics",
          id=",".join(video_ids_slice)
      )
      response = request.execute()
      video_items.extend(response["items"])
      current_window_start_index += MAX_VIDEO_IDS_PER_DETAIL_REQUEST
    return video_items

  def get_comments_for_videos(self, video_ids: list[str]):
    comments = []

    print(f"Grabbing comments for {len(video_ids)} videos...")
    for video_id in video_ids:
      comments.extend(self._get_comments_for_video(video_id))

    return comments

  def _get_comments_for_video(self, video_id: str):
    """Retrieves comments for a specific video.

    Args:
        video_id (str): The ID of the YouTube video.

    Returns:
        list: A list of comment items for the specified video.

    """
    video_comments = []
    next_page_token = ""

    while True:
      try:
        request = self._client.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page_token
        )

        response = request.execute()
        video_comments.extend(response["items"])

        if "nextPageToken" in response:
          next_page_token = response["nextPageToken"]
          print(f"......next page token:  {next_page_token}")
        else:
          break
      except errors.HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred...")
        break

    return video_comments


######### COMMOM FUNCTIONS ######################


def _load_dataset_from_bq(table_name: str) -> pd.DataFrame:
  client = bigquery.Client(project=PROJECT_ID)

  query = (
      f"SELECT * FROM {PROJECT_ID}.{DATASET_ID}.{table_name}"
  )

  query_job = client.query(query)
  return query_job.to_dataframe()


def _write_dataset_to_bq(
    dataset: pd.DataFrame,
    dataset_id: str,
    table_id: str
):
  """Writes a Pandas DataFrame to a BigQuery table.

  Args:
      dataset: The Pandas DataFrame to write.
      dataset_id: The ID of the BigQuery dataset.
      table_id: The ID of the BigQuery table.

  Raises:
      google.api_core.exceptions.GoogleAPICallError: If an error occurs during
      the BigQuery operation.
  """
  client = bigquery.Client(project=PROJECT_ID)

  load_data_job = client.load_table_from_dataframe(
      dataset,
      f"{dataset_id}.{table_id}",
      job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"),
  )

  # Wait for the load job to complete
  load_data_job.result()


def _run_batch_prediction_job(input_bq_uri: str, output_bq_uri: str):
  """Runs a batch prediction job using Vertex AI.

  Args:
      input_bq_uri (str): The BigQuery URI for the input data.
      output_bq_uri (str): The BigQuery URI for the output data.

  Raises:
      ValueError: If the batch prediction job fails.

  """
  vertexai.init(project=PROJECT_ID, location=LOCATION)
  batch_prediction_job = BatchPredictionJob.submit(
      source_model=GEMINI_PRO_MODEL_ID,
      input_dataset=input_bq_uri,
      output_uri_prefix=output_bq_uri
  )
  print(f"Job resource name: {batch_prediction_job.resource_name}")
  print(f"Model resource name: {batch_prediction_job.model_name}")
  print(f"Job state: {batch_prediction_job.state.name}")

  while not batch_prediction_job.has_ended:
    time.sleep(5)
    batch_prediction_job.refresh()
    print("...Waiting")

  if batch_prediction_job.has_succeeded:
    print("Job succeeded!")
  else:
    raise ValueError(f"Job failed: {batch_prediction_job.error}")

######### COMMOM FUNCTIONS ######################


######### VIDEO PROCESSING ######################


def _find_videos(criteria: YoutubeSearchCriteria):
  """Finds videos based on the given search criteria.

  Args:
      criteria (YoutubeSearchCriteria): The search criteria for finding videos.

  Returns:
      pd.DataFrame: A DataFrame containing the video details, including video
      ID, URL, title, description, channel information, and publication date.

  """
  videos = SEARCH_ENGINE.search_for_videos(criteria)
  print(f"Found {len(videos)} videos:")

  yt_data_api_response_items_df = pd.json_normalize(videos)

  yt_data_api_response_df = yt_data_api_response_items_df.assign(
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

  return yt_data_api_response_df


def _populate_video_data_with_stats(video_dataset: pd.DataFrame):
  """Populates the video dataset with statistics retrieved from the YouTube API.

  Args:
      video_dataset (pd.DataFrame): A DataFrame containing video information,
        including a 'videoId' column.

  Returns:
      pd.DataFrame: A DataFrame with the same data as the input, but with
        additional columns for video statistics such as view count, like count,
        favorite count, and comment count.

  """
  video_ids = video_dataset["videoId"].tolist()
  video_stats = SEARCH_ENGINE.get_video_details(video_ids)

  stats_as_df = pd.json_normalize(video_stats)[
      [
          "id",
          "statistics.viewCount",
          "statistics.likeCount",
          "statistics.favoriteCount",
          "statistics.commentCount",
      ]
  ].rename(
      columns={
          "id": "videoId",
          "statistics.viewCount": "viewCount",
          "statistics.likeCount": "likeCount",
          "statistics.favoriteCount": "favoriteCount",
          "statistics.commentCount": "commentCount",
      }
  ).fillna(
      0
  ).astype(
      {
          "viewCount": "int64",
          "likeCount": "int64",
          "favoriteCount": "int64",
          "commentCount": "int64",
      }
  )

  return video_dataset.merge(stats_as_df, on="videoId")


def _prepare_video_data_for_analysis(
    criteria: YoutubeSearchCriteria,
    video_data_bq_table_name: str
) -> pd.DataFrame:
  """Prepares video data for analysis.

  The function will check the flags to determine if it should use cached data
  or make calls to the YT Data API.

  Args:
      criteria (YoutubeSearchCriteria): The search criteria for finding videos.
      video_data_bq_table_name (str): The name of the BigQuery table where
        video data is stored or will be stored.

  Returns:
      pd.DataFrame: A DataFrame containing video data with prompts attached,
        ready for analysis. Also writes the data to the specified BigQuery
        table.
  """
  if USE_CACHED_VIDEO_DATA:
    print("!!!!!!!!!!!!!!! Using cached video data !!!!!!!!!!!!!!!!!!!!!!!!!")
    video_dataset_with_stats = _load_dataset_from_bq(video_data_bq_table_name)
  else:
    print("Using YT API to find videos...")
    video_dataset = _find_videos(criteria)
    video_dataset_with_stats = _populate_video_data_with_stats(video_dataset)

  attach_prompt_task = video.AttachBatchVideoAnalysisRequestStep(REPORT_PARAMS)
  video_dataset_with_prompts = attach_prompt_task.execute(
      video_dataset_with_stats
  )

  _write_dataset_to_bq(
      video_dataset_with_prompts,
      DATASET_ID,
      video_data_bq_table_name
    )

  return video_dataset_with_prompts["videoId"].tolist()


######### COMMENT PROCESSING ######################


def _find_comments(video_sentiment_data: pd.DataFrame) -> pd.DataFrame:
  """Finds comments for a list of videos.

  Args:
      video_sentiment_data (pd.DataFrame): A DataFrame containing video
        information, including a 'videoId' column.

  Returns:
      pd.DataFrame: A DataFrame containing comment details, including comment
        ID, video ID, author information, publication date, text, like count,
        number of replies, and nested replies.

  Raises:
      Exception: If there is an error during the comment retrieval process.
  """
  video_ids = video_sentiment_data["videoId"].tolist()
  comments = SEARCH_ENGINE.get_comments_for_videos(video_ids)

  comments_dataset = pd.json_normalize(
      comments
  )[
      [
          "id",
          "snippet.videoId",
          "snippet.topLevelComment.snippet.authorChannelId.value",
          "snippet.topLevelComment.snippet.publishedAt",
          "snippet.topLevelComment.snippet.textOriginal",
          "snippet.topLevelComment.snippet.likeCount",
          "snippet.totalReplyCount",
          "replies.comments"
      ]
  ].rename(
      columns={
          "id": "commentId",
          "snippet.videoId": "videoId",
          "snippet.topLevelComment.snippet.authorChannelId.value": "authorId",
          "snippet.topLevelComment.snippet.publishedAt": "publishedAt",
          "snippet.topLevelComment.snippet.textOriginal": "text",
          "snippet.topLevelComment.snippet.likeCount": "likeCount",
          "snippet.totalReplyCount": "numOfReplies",
          "replies.comments": "replies"
      }
  ).fillna(
      0
  ).astype(
      {
          "likeCount": "int64",
          "numOfReplies": "int64",
      }
  )

  return comments_dataset


def _merge_comments_with_video_sentiment(
    comments_dataset: pd.DataFrame,
    video_sentiment_dataset: pd.DataFrame) -> pd.DataFrame:
  """Merges comments data with video sentiment data.

  This function takes two DataFrames, one containing comments data and the
  other containing video sentiment data, and merges them based on the 'videoId'
  column. It specifically extracts the 'videoId' and 'summary' columns from the
  video sentiment dataset and renames 'summary' to 'videoSummary' before
  performing the merge.

  Args:
      comments_dataset (pd.DataFrame): DataFrame containing comments data.
      video_sentiment_dataset (pd.DataFrame): DataFrame containing video
        sentiment data.
  Returns:
      pd.DataFrame: A merged DataFrame with comments data and video summary.
  """
  video_id_and_summary_df = video_sentiment_dataset[
      [
          "videoId",
          "summary"
      ]
  ].rename(
      columns={"summary": "videoSummary"}
  )

  return pd.merge(
      left=comments_dataset,
      right=video_id_and_summary_df,
      on="videoId",
      how="left"
  )


def _flatten_replies(comments_dataset: pd.DataFrame) -> pd.DataFrame:
  """Flattens nested comment replies into a single DataFrame.

  This function takes a DataFrame of comments, some of which may have nested
  replies, and transforms it into a flat structure where each comment and
  each reply is a separate row. It handles the extraction of reply details,
  normalization of nested JSON structures, and merging of reply data with
  top-level comment data.

  Args:
      comments_dataset (pd.DataFrame): A DataFrame containing comments data,
        including a 'replies' column with nested comment replies.

  Returns:
      pd.DataFrame: A DataFrame where each row represents either a top-level
        comment or a reply. The DataFrame includes columns for comment ID,
        video ID, author information, publication date, text, like count, and
        a 'parentId' column to link replies to their parent comments.
  """
  comments_top_level = comments_dataset.copy()
  comments_top_level["parentId"] = pd.NA

  # pylint: disable=g-explicit-length-test
  top_level_comments_with_nested_replies = comments_top_level[
      comments_top_level["replies"].apply(
          lambda x: isinstance(x, list) and len(x) > 0
      )
  ].copy()
  replies_exploded = top_level_comments_with_nested_replies.explode(
      "replies", ignore_index=True
  )

  normalized_replies = pd.json_normalize(replies_exploded["replies"])
  processed_replies = normalized_replies[
      [
          "id",
          "snippet.videoId",
          "snippet.authorChannelId.value",
          "snippet.publishedAt",
          "snippet.textOriginal",
          "snippet.likeCount",
      ]
  ].rename(
      columns={
          "id": "commentId",
          "snippet.videoId": "videoId",
          "snippet.authorChannelId.value": "authorId",
          "snippet.publishedAt": "publishedAt",
          "snippet.textOriginal": "text",
          "snippet.likeCount": "likeCount"
      }
  ).fillna(
      0
  ).astype(
      {
          "likeCount": "int64",
      }
  )
  processed_replies["parentId"] = (
      processed_replies["commentId"].str.partition(".")[0]
  )
  combined_flattened_replies = pd.concat(
      [comments_top_level, processed_replies], ignore_index=True
  )

  combined_flattened_replies.drop(columns="replies", inplace=True)
  combined_flattened_replies.fillna({"numOfReplies": 0}, inplace=True)
  return combined_flattened_replies


def _prepare_comments_for_analysis(
    video_sentimedata_bq_table: str,
    comments_data_bq_table: str
):
  """Prepares comments data for analysis.

  This function orchestrates the process of preparing comments data for
  sentiment analysis. It loads video sentiment data from BigQuery, retrieves
  comments for those videos, merges the comments with the video sentiment data,
  flattens any nested replies, and then attaches prompts for analysis.
  Finally, it writes the prepared comments data to a specified BigQuery table.

  Args:
      video_sentimedata_bq_table (str): The name of the BigQuery table
        containing video sentiment data.
      comments_data_bq_table (str): The name of the BigQuery table where the
        prepared comments data will be stored.
  """
  video_sentiment_data = _load_dataset_from_bq(video_sentimedata_bq_table)
  raw_comments_bq_table_name = comments_data_bq_table + "_raw_comments"

  if USE_CACHED_COMMENT_DATA:
    print("!!!!!!!!!!!!!!! Using cached comment data !!!!!!!!!!!!!!!!!!!!!!!!!")
    flattened_comments_dataset = _load_dataset_from_bq(
        raw_comments_bq_table_name
    )
  else:
    print("Using YT API to find comments...")
    comments_dataset = _find_comments(video_sentiment_data)
    flattened_comments_dataset = _flatten_replies(comments_dataset)

    _write_dataset_to_bq(
        flattened_comments_dataset,
        DATASET_ID,
        raw_comments_bq_table_name
    )

  merged_comment_dataset = _merge_comments_with_video_sentiment(
      flattened_comments_dataset,
      video_sentiment_data
  )

  attach_prompt_task = comment.AttachBatchVideoCommentAnalysisRequestStep(
      REPORT_PARAMS
  )
  comment_dataset_with_prompts = attach_prompt_task.execute(
      merged_comment_dataset
  )

  # Dropping video comments to save space, since they're not needed anymore
  if "videoSummary" in comment_dataset_with_prompts.columns:
    comment_dataset_with_prompts.drop(columns="videoSummary", inplace=True)

  _write_dataset_to_bq(
      comment_dataset_with_prompts,
      DATASET_ID,
      comments_data_bq_table
  )


def main() -> None:
  """Main function to test the YoutubeSearch class."""
  if not PROJECT_ID or not API_KEY:
    raise ValueError("Oops...You dind't fill out the API_KEY or PROJECT_ID!")

  if PERFORM_VIDEO_ANALYSIS:
    print("################## Performing VIDEO analysis...")
    criteria = YoutubeSearchCriteria(
        TOPIC
    ).with_language(
        Language.ENGLISH
    ).with_sort_by(
        VideoResultsSortBy.RELEVANCE
    ).with_max_results(
        1
    ).with_published_after(
        RELEASE_DATE
    )
    print(f"Searching for videos with criteria: \n{str(criteria)}\n")

    videos_bq_table = f"{REPORT_TABLE_NAME_PREFIX}_videos_with_file_parts"
    _prepare_video_data_for_analysis(criteria, videos_bq_table)

    input_bq_uri = f"bq://{PROJECT_ID}.{DATASET_ID}.{videos_bq_table}"
    output_bq_uri = f"bq://{PROJECT_ID}.{DATASET_ID}.{videos_bq_table}_results"
    _run_batch_prediction_job(input_bq_uri, output_bq_uri)

  if PERFORM_COMMENT_ANALYSIS:
    print("################## Performing COMMENT analysis...")
    video_sentiment_data_bq_table_name = (
        f"{REPORT_TABLE_NAME_PREFIX}_video_sentiment_data"
    )
    comments_bq_table_name = f"{REPORT_TABLE_NAME_PREFIX}_comments"

    _prepare_comments_for_analysis(
        video_sentiment_data_bq_table_name,
        comments_bq_table_name
    )

    input_bq_uri = f"bq://{PROJECT_ID}.{DATASET_ID}.{comments_bq_table_name}"
    output_bq_uri = (
        f"bq://{PROJECT_ID}.{DATASET_ID}.{comments_bq_table_name}_results"
    )
    _run_batch_prediction_job(input_bq_uri, output_bq_uri)


SEARCH_ENGINE = YoutubeSearch(API_KEY)

REPORT_PARAMS = wfe.WorkflowExecution()
REPORT_PARAMS.executionId = "some_id"
REPORT_PARAMS.data_outputs.extend([
    wfe.SentimentDataType.SENTIMENT_DATA_TYPE_SENTIMENT_SCORE,
    wfe.SentimentDataType.SENTIMENT_DATA_TYPE_DISTRIBUTION,
])


# report.ReportParameters(
#     sources=[
#         workflow_execution.SocialContentSource.VIDEO_CONTENT,
#         workflow_execution.SocialContentSource.VIDEO_COMMENT,
#     ],
#     analysis_windows=[
#         report.AnalysisWindow(
#             date_range_start=RELEASE_DATE,
#             date_range_end=datetime.date.today(),
#             topics=[TOPIC]
#         )
#     ]
# )


if __name__ == "__main__":
  main()
