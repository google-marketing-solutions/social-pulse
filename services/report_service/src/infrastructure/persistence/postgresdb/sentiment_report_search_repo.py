"""Module for sentiment report search repo implementations in PostgresDB."""

from typing import Any, List

from domain.ports import persistence
from socialpulse_common.messages import common as common_msg
from socialpulse_common.messages import sentiment_report as report_msg
from socialpulse_common.persistence import postgresdb_client as client

# Column indices for the SentimentReports table (matching sentiment_report_repo.py)
REPORTID_COL_INDEX = 0
SOURCES_COL_INDEX = 1
DATAOUTPUTS_COL_INDEX = 2
TOPIC_COL_INDEX = 3
DATERANGESTART_COL_INDEX = 4
DATERANGEEND_COL_INDEX = 5
STATUS_COL_INDEX = 6
CREATEDON_COL_INDEX = 7
LASTUPDATEDON_COL_INDEX = 8


class PostgresDbSentimentReportSearchRepo(
    persistence.SentimentReportSearchRepo
):
  """Implementation of a sentiment report search repo in PostgresDB."""

  def __init__(self, postgres_client: client.PostgresDbClient):
    self._postgres_client = postgres_client

  def get_reports(
      self,
      criteria: persistence.SentimentReportSearchCriteria
  ) -> List[report_msg.SentimentReport]:
    """Retrieves sentiment reports by the provided filters.

    Args:
      criteria: Criteria by which to filter/sort the results.
    Returns:
      A list of sentiment reports matching the provided criteria.
    """
    query = """
      SELECT
          reportid,
          sources,
          dataoutputs,
          topic,
          daterangestart,
          daterangeend,
          status,
          createdon,
          lastupdatedon
      FROM
          public.SentimentReports
      WHERE 1=1
    """
    params = []

    if criteria.status:
      query += " AND status = %s"
      params.append(criteria.status.value)

    if criteria.topic_contains:
      query += " AND topic ILIKE %s"
      params.append(f"%{criteria.topic_contains}%")

    if criteria.sort_by:
      sort_column = "createdon"  # Default
      if criteria.sort_by == persistence.SentimentReportsSortBy.STATUS:
        sort_column = "status"
      elif criteria.sort_by == persistence.SentimentReportsSortBy.TOPIC:
        sort_column = "topic"
      elif criteria.sort_by == persistence.SentimentReportsSortBy.START_DATE:
        sort_column = "daterangestart"
      elif criteria.sort_by == persistence.SentimentReportsSortBy.END_DATE:
        sort_column = "daterangeend"

      direction = "ASC" if criteria.sort_ascending else "DESC"
      query += f" ORDER BY {sort_column} {direction}"
    else:
      # Default sort by created descending if not specified
      query += " ORDER BY createdon DESC"

    rows = self._postgres_client.retrieve_rows(query, tuple(params))

    return [self._create_sentiment_report_from_row(row) for row in rows]

  def _create_sentiment_report_from_row(
      self, row: tuple[Any, ...]
  ) -> report_msg.SentimentReport:
    """Creates a SentimentReport message from a database row."""
    report_id = row[REPORTID_COL_INDEX]
    datasets = self._get_report_datasets(report_id)

    return report_msg.SentimentReport(
        report_id=report_id,
        status=row[STATUS_COL_INDEX],
        sources=[
            common_msg.SocialMediaSource[source]
            for source in row[SOURCES_COL_INDEX]
        ],
        data_output=(
            common_msg.SentimentDataType[row[DATAOUTPUTS_COL_INDEX][0]]
            if row[DATAOUTPUTS_COL_INDEX] else None
        ),
        topic=row[TOPIC_COL_INDEX],
        start_time=row[DATERANGESTART_COL_INDEX],
        end_time=row[DATERANGEEND_COL_INDEX],
        created_on=row[CREATEDON_COL_INDEX],
        last_updated_on=row[LASTUPDATEDON_COL_INDEX],
        datasets=datasets,
    )

  def _get_report_datasets(
      self, report_id: str
  ) -> List[report_msg.SentimentReportDataset]:
    """Retrieves the datasets associated with a given report ID."""
    query = """
      SELECT
          reportId,
          source,
          dataOutput,
          outputUri
      FROM
          SentimentReportDatasets
      WHERE
          reportId = %s
    """

    rows = self._postgres_client.retrieve_rows(query, (report_id,))
    if not rows:
      return []

    return [
        report_msg.SentimentReportDataset(
            report_id=row[0],
            source=common_msg.SocialMediaSource[row[1]],
            data_output=common_msg.SentimentDataType[row[2]],
            dataset_uri=row[3],
        )
        for row in rows
    ]
