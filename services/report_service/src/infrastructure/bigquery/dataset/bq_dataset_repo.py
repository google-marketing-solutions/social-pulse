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

import logging

from domain.ports import dataset
from socialpulse_common.messages import common as msg_common
from socialpulse_common.messages import sentiment_report as report_msg
from socialpulse_common.persistence import bigquery_client

logger = logging.getLogger(__name__)


class BigQueryDatasetRepo(dataset.DatasetRepo):
  """BigQuery implementation of DatasetRepo."""

  def __init__(self, bq_client: bigquery_client.BigQueryClient):
    self._bq_client = bq_client

  def get_analysis_results(
      self,
      datasets: list[report_msg.SentimentReportDataset],
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
      include_justifications: bool = True,
  ) -> report_msg.AnalysisResults:
    """Retrieves analysis results for the provided datasets.

    Args:
      datasets: List of datasets to retrieve analysis results for.
      start_date: Optional start date filter (ISO format).
      end_date: Optional end date filter (ISO format).
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.
      include_justifications: Whether to include justifications in the
        results.

    Returns:
      AnalysisResults object containing the analysis results for the
      provided datasets.
    """
    results = report_msg.AnalysisResults()

    for ds in datasets:
      if not ds.dataset_uri or not ds.source or not ds.data_output:
        continue

      table_id = self._convert_uri_to_table_id(ds.dataset_uri)
      source_result = self._fetch_dataset_result(
          table_id,
          ds.data_output,
          start_date=start_date,
          end_date=end_date,

          channel_title=channel_title,
          include_justifications=include_justifications,
      )

      # Mapping Source Enum to Field Name
      field_name = ds.source.value.lower()

      # Verify field exists (AnalysisResults fields are snake_case of enum)
      if hasattr(results, field_name):
        setattr(results, field_name, source_result)
      else:
        logger.warning("Unknown source or field not found for: %s", ds.source)

    return results

  def get_channels(
      self,
      datasets: list[report_msg.SentimentReportDataset],
      query: str | None = None,
  ) -> list[str]:
    """Retrieves a list of unique channels for the provided datasets.

    Args:
      datasets: List of datasets to retrieve channels for.
      query: Optional query to filter channels by.

    Returns:
      List of unique channel names.
    """
    channels = set()
    for ds in datasets:
      if not ds.dataset_uri:
        continue

      table_id = self._convert_uri_to_table_id(ds.dataset_uri)
      try:
        ds_channels = self._query_channels(table_id, query)
        channels.update(ds_channels)
      except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to fetch channels for table %s: %s", table_id, e)

    return sorted(list(channels))

  def _convert_uri_to_table_id(self, uri: str) -> str:
    """Converts bq://project/dataset/table to project.dataset.table.

    Args:
      uri: URI to convert.

    Returns:
      Table ID in project.dataset.table format.
    """
    # Expected format: bq://project-id/dataset/table
    if uri.startswith("bq://"):
      return uri[5:].replace("/", ".")
    return uri

  def _fetch_dataset_result(
      self,
      table_id: str,
      data_output: msg_common.SentimentDataType,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
      include_justifications: bool = True,
  ) -> report_msg.SourceAnalysisResult:
    """Fetches and parses result from BigQuery for a single dataset.

    Args:
      table_id: Table ID in project.dataset.table format.
      data_output: Data output type.
      start_date: Optional start date filter.
      end_date: Optional end date filter.
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.
      include_justifications: Whether to include justifications in the
        results.

    Returns:
      SourceAnalysisResult object containing the analysis results for the
      provided dataset.
    """
    result = report_msg.SourceAnalysisResult()

    if data_output == msg_common.SentimentDataType.SHARE_OF_VOICE:
      logger.info("Fetching SHARE_OF_VOICE for %s", table_id)
      rows = self._query_share_of_voice(
          table_id,
          start_date=start_date,
          end_date=end_date,
          channel_title=channel_title,
          excluded_channels=excluded_channels,
      )
      result.share_of_voice = [
          report_msg.ShareOfVoiceItem(
              name=row.get("productOrBrand", "Unknown"),
              positive=int(row.get("Positive_Views", 0)),
              negative=int(row.get("Negative_Views", 0)),
              neutral=int(row.get("Neutral_Views", 0)),
          )
          for row in rows
      ]

    elif data_output == msg_common.SentimentDataType.SENTIMENT_SCORE:
      logger.info("Fetching SENTIMENT_SCORE for %s", table_id)
      rows = self._query_sentiment_score(
          table_id,
          start_date=start_date,
          end_date=end_date,
          channel_title=channel_title,
          excluded_channels=excluded_channels,
      )
      logger.info("Got %s rows for SENTIMENT_SCORE", len(rows))

      result.sentiment_over_time = self._build_sentiment_timeline(rows)
      result.overall_sentiment = self._build_overall_sentiment(rows)
      result.justification_breakdown = self._build_justification_breakdown(
          table_id,
          start_date=start_date,
          end_date=end_date,
          channel_title=channel_title,

          excluded_channels=excluded_channels,
          include_justifications=include_justifications,
      )

    return result

  def _build_sentiment_timeline(
      self, rows: list[dict[str, any]]
  ) -> list[report_msg.SentimentOverTime]:
    """Builds sentiment timeline from BigQuery rows."""
    sentiment_over_time = []
    for row in rows:
      pos = int(row.get("POSITIVE_VIEWS", 0))
      neg = int(row.get("NEGATIVE_VIEWS", 0))
      neu = int(row.get("NEUTRAL_VIEWS", 0))

      sentiment_over_time.append(
          report_msg.SentimentOverTime(
              date=row.get("published_week", ""),
              positive=pos,
              negative=neg,
              neutral=neu,
          )
      )
    return sentiment_over_time

  def _build_overall_sentiment(
      self, rows: list[dict[str, any]]
  ) -> report_msg.OverallSentiment:
    """Builds overall sentiment from BigQuery rows."""
    overall_pos = sum(int(row.get("POSITIVE_VIEWS", 0)) for row in rows)
    overall_neg = sum(int(row.get("NEGATIVE_VIEWS", 0)) for row in rows)
    overall_neu = sum(int(row.get("NEUTRAL_VIEWS", 0)) for row in rows)

    total = overall_pos + overall_neg + overall_neu
    average = 0.0
    if total > 0:
      average = (overall_pos - overall_neg) / total

    return report_msg.OverallSentiment(
        positive=overall_pos,
        negative=overall_neg,
        neutral=overall_neu,
        average=average,
    )

  def _build_justification_breakdown(
      self,
      table_id: str,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
      include_justifications: bool = True,
  ) -> report_msg.JustificationBreakdown:
    """Builds justification breakdown from BigQuery rows."""
    if not include_justifications:
      return report_msg.JustificationBreakdown()

    logger.info("Building justification breakdown")
    justification_breakdown = report_msg.JustificationBreakdown()

    try:
      # Positive justifications
      pos_rows = self._query_justification_breakdown(
          table_id,
          sentiment_filter="POSITIVE",
          start_date=start_date,
          end_date=end_date,
          channel_title=channel_title,
          excluded_channels=excluded_channels,
      )
      justification_breakdown.positive = [
          report_msg.JustificationItem(
              category=row.get("category", "Unknown"),
              count=int(row.get("sum_of_views", 0)),
          )
          for row in pos_rows
      ]

      # Negative justifications
      neg_rows = self._query_justification_breakdown(
          table_id,
          sentiment_filter="NEGATIVE",
          start_date=start_date,
          end_date=end_date,
          channel_title=channel_title,
          excluded_channels=excluded_channels,
      )
      justification_breakdown.negative = [
          report_msg.JustificationItem(
              category=row.get("category", "Unknown"),
              count=int(row.get("sum_of_views", 0)),
          )
          for row in neg_rows
      ]
    except Exception as e:  # pylint: disable=broad-exception-caught
      logger.warning(
          "Failed to fetch justification breakdown for table %s: %s",
          table_id,
          e,
      )
      # Ensure we return empty breakdown rather than partial/undefined
      justification_breakdown = report_msg.JustificationBreakdown()

    return justification_breakdown

  def _query_justification_breakdown(
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
    where_clauses = [f"t0.sentimentScore LIKE '%{sentiment_filter}%'"]

    if start_date:
      where_clauses.append(f"t.publishedAt >= '{start_date}'")
    if end_date:
      where_clauses.append(f"t.publishedAt <= '{end_date}'")
    if channel_title:
      where_clauses.append(f"t.channelTitle = '{channel_title}'")
    if excluded_channels:
      sanitized = [c.replace("'", "\\'") for c in excluded_channels]
      channels_str = "', '".join(sanitized)
      where_clauses.append(f"t.channelTitle NOT IN ('{channels_str}')")

    where_clause = " AND ".join(where_clauses)

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

  def _query_share_of_voice(
      self,
      table_id: str,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> list[dict[str, any]]:
    """Executes query for SHARE_OF_VOICE.

    Args:
      table_id: Table ID in project.dataset.table format.
      start_date: Optional start date filter.
      end_date: Optional end date filter.
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.

    Returns:
      List of dictionaries containing the share of voice results.
    """
    where_clauses = ["s.productOrBrand IS NOT NULL", "relevanceScore >= 90"]

    if start_date:
      where_clauses.append(f"publishedAt >= '{start_date}'")
    if end_date:
      where_clauses.append(f"publishedAt <= '{end_date}'")
    if channel_title:
      # Assuming channelTitle is a field in the table
      where_clauses.append(f"channelTitle = '{channel_title}'")
    if excluded_channels:
      # Simple optimization: escape single quotes in channel names to
      # prevent SQL syntax errors
      sanitized = [c.replace("'", "\\'") for c in excluded_channels]
      channels_str = "', '".join(sanitized)
      where_clauses.append(f"channelTitle NOT IN ('{channels_str}')")

    where_clause = " AND ".join(where_clauses)

    query = f"""
        SELECT
          s.productOrBrand,
          SUM(CASE
              WHEN s.sentimentScore IN ( 'EXTREME_POSITIVE', 'POSITIVE', 'PARTIAL_POSITIVE' ) THEN COALESCE(t.viewCount, 0)
              ELSE 0
          END
            ) AS Positive_Views,
          SUM(CASE
              WHEN s.sentimentScore IN ('NEUTRAL') OR s.sentimentScore IS NULL THEN COALESCE(t.viewCount, 0)
              ELSE 0
          END
            ) AS Neutral_Views,
          SUM(CASE
              WHEN s.sentimentScore IN ( 'EXTREME_NEGATIVE', 'NEGATIVE', 'PARTIAL_NEGATIVE' ) THEN COALESCE(t.viewCount, 0)
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

  def _query_sentiment_score(
      self,
      table_id: str,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> list[dict[str, any]]:
    """Executes query for SENTIMENT_SCORE.

    Args:
      table_id: Table ID in project.dataset.table format.
      start_date: Optional start date filter.
      end_date: Optional end date filter.
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.

    Returns:
      List of dictionaries containing the sentiment score results.
    """
    where_clauses = ["videos.relevanceScore >= 90"]

    if start_date:
      where_clauses.append(f"videos.publishedAt >= '{start_date}'")
    if end_date:
      where_clauses.append(f"videos.publishedAt <= '{end_date}'")
    if channel_title:
      where_clauses.append(f"videos.channelTitle = '{channel_title}'")
    if excluded_channels:
      sanitized = [c.replace("'", "\\'") for c in excluded_channels]
      channels_str = "', '".join(sanitized)
      where_clauses.append(f"videos.channelTitle NOT IN ('{channels_str}')")

    where_clause = " AND ".join(where_clauses)

    query = f"""
        SELECT
          FORMAT_TIMESTAMP('%Y-%m-%d', TIMESTAMP_TRUNC(CAST(publishedAt AS TIMESTAMP), WEEK)) AS published_week,

          -- Sum views for all POSITIVE scores
          SUM(CASE
            WHEN sent.sentimentScore IN (
                'EXTREME_POSITIVE',
                'POSITIVE',
                'PARTIAL_POSITIVE'
              ) THEN COALESCE(videos.viewCount, 0)
            ELSE 0
          END) AS POSITIVE_VIEWS,

          -- Sum views for all NEGATIVE scores
          SUM(CASE
            WHEN sent.sentimentScore IN (
                'EXTREME_NEGATIVE',
                'NEGATIVE',
                'PARTIAL_NEGATIVE'
              ) THEN COALESCE(videos.viewCount, 0)
            ELSE 0
          END) AS NEGATIVE_VIEWS,

          -- Sum views for NEUTRAL (as a catch-all)
          SUM(CASE
            WHEN sent.sentimentScore IN (
                'NEUTRAL'
              ) THEN COALESCE(videos.viewCount, 0)
            ELSE 0
          END) AS NEUTRAL_VIEWS,

          -- Total sum for verification
          SUM(COALESCE(videos.viewCount, 0)) AS TOTAL_VIEWS

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
      # Sanitize query to prevent basic injection if not parametrized
      # BQ client parametrizes usually, but here we are constructing
      # string.
      # Actually client.query() takes string.
      # Ideally we should use parameters but for now simple escaping or
      # simple logic.
      # Let's just use simple LIKE with lower case for case-insensitive
      # search.
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
