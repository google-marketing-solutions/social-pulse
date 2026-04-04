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
"""BigQuery implementation of Dataset Persistence."""

import json
import logging

from domain.ports import dataset
from socialpulse_common.messages import sentiment_report as report_msg
from socialpulse_common.persistence import bigquery_client
from socialpulse_common.utils import markdown


logger = logging.getLogger(__name__)


class BigQueryDatasetRepo(dataset.DatasetRepo):
  """BigQuery implementation of DatasetRepo."""

  def __init__(self, bq_client: bigquery_client.BigQueryClient):
    self._bq_client = bq_client

  def query_justification_breakdown_for_videos(
      self,
      table_id: str,
      sentiment_filter: str,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> list[dict[str, any]]:
    """Executes query for Justification Breakdown.

    Args:
      table_id: Table ID in project.dataset.table format.
      sentiment_filter: 'POSITIVE' or 'NEGATIVE' to filter sentiments.
      start_date: Optional start date filter.
      end_date: Optional end date filter.
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.

    Returns:
      List of dictionaries containing the justification results.
    """
    where_clause = self._build_where_clause(
        base_clauses=[f"t0.sentimentScore LIKE '%{sentiment_filter}%'"],
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
        field_prefix="t.",
    )

    query = f"""
        SELECT
          t1.category,
          SUM(t.viewCount) AS sum_of_views
        FROM
          `{table_id}` AS t,
          UNNEST(t.sentiments) AS t0,
          UNNEST(t0.justifications) AS t1
        WHERE
          {where_clause}
        GROUP BY
          t1.category
        ORDER BY
          sum_of_views DESC
        LIMIT 10
        """
    return self._bq_client.query(query)

  def query_justification_breakdown_for_comments(
      self,
      table_id: str,
      sentiment_filter: str,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> list[dict[str, any]]:
    """Executes query for Justification Breakdown for comments.

    Args:
      table_id: Table ID in project.dataset.table format.
      sentiment_filter: 'POSITIVE' or 'NEGATIVE' to filter sentiments.
      start_date: Optional start date filter.
      end_date: Optional end date filter.
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.

    Returns:
      List of dictionaries containing the justification results.
    """
    where_clause = self._build_where_clause(
        base_clauses=[f"t0.sentimentScore LIKE '%{sentiment_filter}%'"],
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
        field_prefix="comments.",
    )

    query = f"""
        SELECT
          t1.category,
          COUNT(*) AS sum_of_comments
        FROM
          `{table_id}` AS comments,
          UNNEST(comments.sentiments) AS t0,
          UNNEST(t0.justifications) AS t1
        WHERE
          {where_clause}
        GROUP BY
          t1.category
        ORDER BY
          sum_of_comments DESC
        LIMIT 10
        """
    return self._bq_client.query(query)

  def query_share_of_voice(
      self,
      table_id: str,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
      relevance_threshold: int = 90,
  ) -> list[dict[str, any]]:
    """Executes query for SHARE_OF_VOICE.

    Args:
      table_id: Table ID in project.dataset.table format.
      start_date: Optional start date filter.
      end_date: Optional end date filter.
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.
      relevance_threshold: The relevance threshold for the report.

    Returns:
      List of dictionaries containing the share of voice results.
    """
    where_clause = self._build_where_clause(
        base_clauses=[
            "s.productOrBrand IS NOT NULL",
            f"relevanceScore >= {relevance_threshold}",
        ],
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
    )

    query = f"""
        SELECT
          s.productOrBrand,
          SUM(CASE
              WHEN LOWER(s.sentimentScore) LIKE '%positive%' THEN COALESCE(t.viewCount, 0)
              ELSE 0
          END
            ) AS Positive_Views,
          SUM(CASE
              WHEN LOWER(s.sentimentScore) NOT LIKE '%positive%' AND LOWER(s.sentimentScore) NOT LIKE '%negative%' OR s.sentimentScore IS NULL THEN COALESCE(t.viewCount, 0)
              ELSE 0
          END
            ) AS Neutral_Views,
          SUM(CASE
              WHEN LOWER(s.sentimentScore) LIKE '%negative%' AND LOWER(s.sentimentScore) NOT LIKE '%positive%' THEN COALESCE(t.viewCount, 0)
              ELSE 0
          END
            ) AS Negative_Views,
          SUM(COALESCE(t.viewCount, 0)) AS Total_Views_Associated_With_Brand
        FROM
          `{table_id}` AS t,
          UNNEST(t.sentiments) AS s
        WHERE
          {where_clause}
        GROUP BY
          s.productOrBrand
        ORDER BY
          Total_Views_Associated_With_Brand DESC
        LIMIT 15
    """
    return self._bq_client.query(query)

  def query_share_of_voice_totals(
      self,
      table_id: str,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
      relevance_threshold: int = 90,
  ) -> dict[str, int]:
    """Queries total item count and views for Share of Voice context.

    Args:
      table_id: Table ID.
      start_date: Start date filter.
      end_date: End date filter.
      channel_title: Channel title filter.
      excluded_channels: Excluded channels.
      relevance_threshold: The relevance threshold for the report.

    Returns:
      Dictionary with positive, negative, neutral views and item_count.
    """
    where_clause = self._build_where_clause(
        base_clauses=[
            "s.productOrBrand IS NOT NULL",
            f"relevanceScore >= {relevance_threshold}",
        ],
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
    )

    query = f"""
        SELECT
          COUNT(DISTINCT t.videoId) AS item_count,
          SUM(CASE
              WHEN LOWER(s.sentimentScore) LIKE '%positive%' THEN COALESCE(t.viewCount, 0)
              ELSE 0
          END) AS positive,
          SUM(CASE
              WHEN LOWER(s.sentimentScore) NOT LIKE '%positive%' AND LOWER(s.sentimentScore) NOT LIKE '%negative%' OR s.sentimentScore IS NULL THEN COALESCE(t.viewCount, 0)
              ELSE 0
          END) AS neutral,
          SUM(CASE
              WHEN LOWER(s.sentimentScore) LIKE '%negative%' AND LOWER(s.sentimentScore) NOT LIKE '%positive%' THEN COALESCE(t.viewCount, 0)
              ELSE 0
          END) AS negative
        FROM
          `{table_id}` AS t,
          UNNEST(t.sentiments) AS s
        WHERE
          {where_clause}
    """
    rows = list(self._bq_client.query(query))
    if not rows:
      return {"item_count": 0, "positive": 0, "negative": 0, "neutral": 0}

    row = rows[0]
    return {
        "item_count": int(row.get("item_count", 0)),
        "positive": int(row.get("positive", 0)),
        "negative": int(row.get("negative", 0)),
        "neutral": int(row.get("neutral", 0)),
    }

  def query_sentiment_breakdown_for_videos(
      self,
      table_id: str,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
      relevance_threshold: int = 90,
  ) -> list[dict[str, any]]:
    """Executes query for SENTIMENT_SCORE.

    Args:
      table_id: Table ID in project.dataset.table format.
      start_date: Optional start date filter.
      end_date: Optional end date filter.
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.
      relevance_threshold: The relevance threshold for the report.

    Returns:
      List of dictionaries containing the sentiment score results.
    """
    where_clause = self._build_where_clause(
        base_clauses=[f"videos.relevanceScore >= {relevance_threshold}"],
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
        field_prefix="videos.",
    )

    query = f"""
        SELECT
          FORMAT_TIMESTAMP(
              '%Y-%m-%d',
              TIMESTAMP_TRUNC(CAST(publishedAt AS TIMESTAMP), WEEK)
          ) AS published_week,

          -- Sum views for all POSITIVE scores
          SUM(CASE
            WHEN LOWER(sent.sentimentScore) LIKE '%positive%' THEN COALESCE(videos.viewCount, 0)
            ELSE 0
          END) AS POSITIVE_VIEWS,

          -- Sum views for all NEGATIVE scores
          SUM(CASE
            WHEN LOWER(sent.sentimentScore) LIKE '%negative%' AND LOWER(sent.sentimentScore) NOT LIKE '%positive%' THEN COALESCE(videos.viewCount, 0)
            ELSE 0
          END) AS NEGATIVE_VIEWS,

          -- Sum views for NEUTRAL (as a catch-all)
          SUM(CASE
            WHEN LOWER(sent.sentimentScore) NOT LIKE '%positive%' AND LOWER(sent.sentimentScore) NOT LIKE '%negative%' OR sent.sentimentScore IS NULL THEN COALESCE(videos.viewCount, 0)
            ELSE 0
          END) AS NEUTRAL_VIEWS,

          -- Total sum for verification
          SUM(COALESCE(videos.viewCount, 0)) AS TOTAL_VIEWS,

          -- Total items count
          COUNT(*) AS TOTAL_ITEMS

        FROM
          `{table_id}` AS videos,
          UNNEST(videos.sentiments) AS sent
        WHERE
          {where_clause}
        GROUP BY
          published_week
        ORDER BY
          published_week
    """
    return self._bq_client.query(query)

  def query_sentiment_breakdown_for_comments(
      self,
      table_id: str,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
      relevance_threshold: int = 90,
  ) -> list[dict[str, any]]:
    """Executes query for SENTIMENT_SCORE for comments.

    Args:
      table_id: Table ID in project.dataset.table format.
      start_date: Optional start date filter.
      end_date: Optional end date filter.
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.
      relevance_threshold: The relevance threshold for the report.

    Returns:
      List of dictionaries containing the sentiment score results.
    """
    where_clause = self._build_where_clause(
        base_clauses=[f"comments.relevanceScore >= {relevance_threshold}"],
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
        field_prefix="comments.",
    )

    query = f"""
        SELECT
          FORMAT_TIMESTAMP(
              '%Y-%m-%d',
              TIMESTAMP_TRUNC(CAST(publishedAt AS TIMESTAMP), WEEK)
          ) AS published_week,

          -- Count for all POSITIVE scores
          SUM(CASE
            WHEN LOWER(sent.sentimentScore) LIKE '%positive%' THEN 1
            ELSE 0
          END) AS POSITIVE_COUNT,

          -- Count for all NEGATIVE scores
          SUM(CASE
            WHEN LOWER(sent.sentimentScore) LIKE '%negative%' AND LOWER(sent.sentimentScore) NOT LIKE '%positive%' THEN 1
            ELSE 0
          END) AS NEGATIVE_COUNT,

          -- Count for NEUTRAL (as a catch-all)
          SUM(CASE
            WHEN LOWER(sent.sentimentScore) NOT LIKE '%positive%' AND LOWER(sent.sentimentScore) NOT LIKE '%negative%' OR sent.sentimentScore IS NULL THEN 1
            ELSE 0
          END) AS NEUTRAL_COUNT,

          -- Total items count
          COUNT(*) AS TOTAL_ITEMS

        FROM
          `{table_id}` AS comments,
          UNNEST(comments.sentiments) AS sent
        WHERE
          {where_clause}
        GROUP BY
          published_week
        ORDER BY
          published_week
    """
    return self._bq_client.query(query)

  def query_sentiment_score_summary_for_videos(
      self,
      table_id: str,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
      relevance_threshold: int = 90,
  ) -> list[dict[str, any]]:
    """Queries for summary stats of sentiment scores for videos.

    Args:
      table_id: Table ID in project.dataset.table format.
      start_date: Optional start date filter.
      end_date: Optional end date filter.
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.
      relevance_threshold: The relevance threshold for the report.

    Returns:
      List of dictionaries containing the sentiment score results.
    """
    where_clause = self._build_where_clause(
        base_clauses=[f"videos.relevanceScore >= {relevance_threshold}"],
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
        field_prefix="videos.",
    )

    query = f"""
        SELECT
          -- Sum views for all POSITIVE scores
          SUM(CASE
            WHEN LOWER(sent.sentimentScore) LIKE '%positive%' THEN COALESCE(videos.viewCount, 0)
            ELSE 0
          END) AS POSITIVE_VIEWS,

          -- Sum views for all NEGATIVE scores
          SUM(CASE
            WHEN LOWER(sent.sentimentScore) LIKE '%negative%' AND LOWER(sent.sentimentScore) NOT LIKE '%positive%' THEN COALESCE(videos.viewCount, 0)
            ELSE 0
          END) AS NEGATIVE_VIEWS,

          -- Sum views for NEUTRAL (as a catch-all)
          SUM(CASE
            WHEN LOWER(sent.sentimentScore) NOT LIKE '%positive%' AND LOWER(sent.sentimentScore) NOT LIKE '%negative%' OR sent.sentimentScore IS NULL THEN COALESCE(videos.viewCount, 0)
            ELSE 0
          END) AS NEUTRAL_VIEWS,

          -- Total sum for verification
          SUM(COALESCE(videos.viewCount, 0)) AS TOTAL_VIEWS,

          -- Total items count
          COUNT(*) AS TOTAL_ITEMS

        FROM
          `{table_id}` AS videos,
          UNNEST(videos.sentiments) AS sent
        WHERE
          {where_clause}
    """
    return self._bq_client.query(query)

  def query_sentiment_score_summary_for_comments(
      self,
      table_id: str,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
      relevance_threshold: int = 90,
  ) -> list[dict[str, any]]:
    """Queries for summary stats of sentiment scores for comments.

    Args:
      table_id: Table ID in project.dataset.table format.
      start_date: Optional start date filter.
      end_date: Optional end date filter.
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.
      relevance_threshold: The relevance threshold for the report.

    Returns:
      List of dictionaries containing the sentiment score results.
    """
    where_clause = self._build_where_clause(
        base_clauses=[f"comments.relevanceScore >= {relevance_threshold}"],
        start_date=start_date,
        end_date=end_date,
        channel_title=channel_title,
        excluded_channels=excluded_channels,
        field_prefix="comments.",
    )

    query = f"""
        SELECT
          -- Count for all POSITIVE scores
          SUM(CASE
            WHEN LOWER(sent.sentimentScore) LIKE '%positive%' THEN 1
            ELSE 0
          END) AS POSITIVE_COUNT,

          -- Count for all NEGATIVE scores
          SUM(CASE
            WHEN LOWER(sent.sentimentScore) LIKE '%negative%' AND LOWER(sent.sentimentScore) NOT LIKE '%positive%' THEN 1
            ELSE 0
          END) AS NEGATIVE_COUNT,

          -- Count for NEUTRAL (as a catch-all)
          SUM(CASE
            WHEN LOWER(sent.sentimentScore) NOT LIKE '%positive%' AND LOWER(sent.sentimentScore) NOT LIKE '%negative%' OR sent.sentimentScore IS NULL THEN 1
            ELSE 0
          END) AS NEUTRAL_COUNT,

          -- Total items count
          COUNT(*) AS TOTAL_ITEMS

        FROM
          `{table_id}` AS comments,
          UNNEST(comments.sentiments) AS sent
        WHERE
          {where_clause}
    """
    return self._bq_client.query(query)

  def get_channels(
      self,
      datasets: list[report_msg.SentimentReportDataset],
      query: str | None = None,
  ) -> list[str]:
    """Retrieves a list of unique channels for the provided datasets.

    Args:
      datasets: List of datasets.
      query: Optional search query.

    Returns:
      List of channel titles.
    """
    all_channels = set()
    for d in datasets:
      if not d.dataset_uri:
        continue
      table_id = d.dataset_uri
      if table_id.startswith("bq://"):
        table_id = table_id[5:].replace("/", ".")

      channels = self._query_channels(table_id, query)
      all_channels.update(channels)

    return sorted(list(all_channels))

  def _build_where_clause(
      self,
      base_clauses: list[str],
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
      field_prefix: str = "",
  ) -> str:
    """Builds a WHERE clause combining base conditions and common filters.

    Args:
      base_clauses: List of initial WHERE conditions.
      start_date: Optional start date filter.
      end_date: Optional end date filter.
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.
      field_prefix: Prefix for fields (e.g., 'videos.', 'comments.', or 't.').

    Returns:
      A SQL WHERE clause string.
    """
    where_clauses = list(base_clauses)

    if start_date:
      where_clauses.append(f"{field_prefix}publishedAt >= '{start_date}'")

    if end_date:
      where_clauses.append(f"{field_prefix}publishedAt <= '{end_date}'")

    if channel_title:
      where_clauses.append(f"{field_prefix}channelTitle = '{channel_title}'")

    if excluded_channels:
      sanitized = [c.replace("'", "\\'") for c in excluded_channels]
      channels_str = "', '".join(sanitized)
      where_clauses.append(
          f"{field_prefix}channelTitle NOT IN ('{channels_str}')"
      )

    return " AND ".join(where_clauses)

  def _query_channels(
      self, table_id: str, query: str | None = None
  ) -> list[str]:
    """Queries distinct channel titles from the table.

    Args:
      table_id: Table ID.
      query: Optional search query.

    Returns:
      List of channel titles.
    """
    where_clause = "videos.channelTitle IS NOT NULL"
    if query:
      safe_query = query.replace("'", "\\'")
      where_clause += (
          f" AND LOWER(videos.channelTitle) LIKE LOWER('%{safe_query}%')"
      )

    qt = f"""
        SELECT DISTINCT videos.channelTitle
        FROM `{table_id}` AS videos
        WHERE {where_clause}
        ORDER BY videos.channelTitle
        LIMIT 100
    """
    rows = self._bq_client.query(qt)
    return [row["channelTitle"] for row in rows]

  def get_full_report_context(
      self,
      datasets: list[report_msg.SentimentReportDataset],
  ) -> list[dict[str, any]]:
    """Retrieves the full report context from datasets.

    Args:
      datasets: List of datasets.

    Returns:
      List of dictionaries containing the full context results.
    """
    all_results = []
    for d in datasets:
      if not d.dataset_uri:
        continue
      table_id = d.dataset_uri
      if table_id.startswith("bq://"):
        table_id = table_id[5:].replace("/", ".")

      query = f"SELECT * FROM `{table_id}` WHERE relevanceScore >= 90"
      rows = self._bq_client.query(query)
      all_results.extend(rows)

    return all_results

  def query_justification_category_metadata(
      self,
      table_id: str,
  ) -> list[dict[str, any]]:
    """Queries justification category metadata.

    Args:
      table_id: Table ID in project.dataset.table format.

    Returns:
      List of dictionaries containing the category metadata.
    """
    try:
      query = f"SELECT category_json_data FROM `{table_id}`"
      rows = list(self._bq_client.query(query))
      if not rows:
        return []

      json_data = rows[0].get("category_json_data")
      if not json_data:
        return []

      # Handle potential markdown wrapping
      json_data = markdown.strip_markdown_code_blocks(json_data)

      return json.loads(json_data)
    except Exception as e:  # pylint: disable=broad-except
      logger.warning("Failed to query metadata table %s: %s", table_id, e)
      return []
