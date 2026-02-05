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
      self, datasets: list[report_msg.SentimentReportDataset]
  ) -> report_msg.AnalysisResults:
    """Retrieves analysis results for the provided datasets.

    Args:
      datasets: List of datasets to retrieve analysis results for.

    Returns:
      AnalysisResults object containing the analysis results for the provided
      datasets.
    """
    results = report_msg.AnalysisResults()

    for ds in datasets:
      if not ds.dataset_uri or not ds.source or not ds.data_output:
        continue

      table_id = self._convert_uri_to_table_id(ds.dataset_uri)
      source_result = self._fetch_dataset_result(table_id, ds.data_output)

      # Mapping Source Enum to Field Name
      field_name = ds.source.value.lower()

      # Verify field exists (AnalysisResults fields are snake_case of enum)
      if hasattr(results, field_name):
        setattr(results, field_name, source_result)
      else:
        logger.warning("Unknown source or field not found for: %s", ds.source)

    return results

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
      self, table_id: str, data_output: msg_common.SentimentDataType
  ) -> report_msg.SourceAnalysisResult:
    """Fetches and parses result from BigQuery for a single dataset.

    Args:
      table_id: Table ID in project.dataset.table format.
      data_output: Data output type.

    Returns:
      SourceAnalysisResult object containing the analysis results for the
      provided dataset.
    """
    result = report_msg.SourceAnalysisResult()

    if data_output == msg_common.SentimentDataType.SHARE_OF_VOICE:
      rows = self._query_share_of_voice(table_id)
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
      rows = self._query_sentiment_score(table_id)
      sentiment_over_time = []
      overall_pos = 0
      overall_neg = 0
      overall_neu = 0

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
        overall_pos += pos
        overall_neg += neg
        overall_neu += neu

      result.sentiment_over_time = sentiment_over_time

      total = overall_pos + overall_neg + overall_neu
      average = 0.0
      if total > 0:
        # Simple weighted average: (Pos - Neg) / Total?
        # Or Just (Pos count) / Total?
        # Providing a simple (Pos - Neg) / Total for now (-1 to 1 scale)
        average = (overall_pos - overall_neg) / total

      result.overall_sentiment = report_msg.OverallSentiment(
          positive=overall_pos,
          negative=overall_neg,
          neutral=overall_neu,
          average=average,
      )

    return result

  def _query_share_of_voice(self, table_id: str) -> list[dict]:
    """Executes query for SHARE_OF_VOICE.

    Args:
      table_id: Table ID in project.dataset.table format.

    Returns:
      List of dictionaries containing the share of voice results.
    """
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
          s.productOrBrand IS NOT NULL
          AND relevanceScore >= 90
        GROUP BY
          s.productOrBrand
        ORDER BY
          Total_Views_Associated_With_Brand DESC
        LIMIT 15
    """
    return self._bq_client.query(query)

  def _query_sentiment_score(self, table_id: str) -> list[dict]:
    """Executes query for SENTIMENT_SCORE.

    Args:
      table_id: Table ID in project.dataset.table format.

    Returns:
      List of dictionaries containing the sentiment score results.
    """
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
          videos.relevanceScore >= 90
        GROUP BY
          published_week
        ORDER BY
          published_week
    """
    return self._bq_client.query(query)
