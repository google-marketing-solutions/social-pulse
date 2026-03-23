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

"""Module for sentiment report repo implementations in PostgresDB."""
import logging
from typing import Any

from domain import sentiment_report
from domain.ports import persistence
from socialpulse_common.messages import common as common_msg
from socialpulse_common.messages import sentiment_report as report_msg
from socialpulse_common.persistence import postgresdb_client as client

# Column indices for the SentimentReports table
REPORTID_COL_INDEX = 0
SOURCES_COL_INDEX = 1
DATAOUTPUTS_COL_INDEX = 2
TOPIC_COL_INDEX = 3
DATERANGESTART_COL_INDEX = 4
DATERANGEEND_COL_INDEX = 5
STATUS_COL_INDEX = 6
CREATEDON_COL_INDEX = 7
LASTUPDATEDON_COL_INDEX = 8
INCLUDEJUSTIFICATIONS_COL_INDEX = 9
RELEVANCETHRESHOLD_COL_INDEX = 10

logger = logging.getLogger(__name__)


class PostgresDbSentimentReportRepo(persistence.SentimentReportRepo):
  """Implementation of a sentiment report repo in PostgresDB."""

  def __init__(self, postgres_client: client.PostgresDbClient):
    self._postgres_client = postgres_client

  def load_report(
      self, report_id: str
  ) -> sentiment_report.SentimentReportEntity:
    """Retrieves a sentiment report by its ID."""
    if not report_id:
      raise ValueError("Provided report_id was None or empty.")

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
          lastupdatedon,
          includeJustifications,
          relevanceThreshold
      FROM
          public.SentimentReports
      WHERE
          reportId = %s
    """
    rows = self._postgres_client.retrieve_row(query, (report_id,))
    if not rows:
      raise ValueError(f"Report with ID {report_id} not found.")

    report = self._create_sentiment_report_from_row(rows)

    return report

  def persist_report(self, report: sentiment_report.SentimentReportEntity):
    """Creates or updates a sentiment report.

    Persists a report, by checking if it already has a UUID.  If not, then it
    will insert the report into persistent storage.  If it does have a UUID,
    it will update the report record in storage.

    Args:
      report: The sentiment report to persist.
    """
    if report.entity_id:
      logger.debug("Updating report %s", report.entity_id)
      self._update_report(report)
    else:
      logger.debug("Inserting report since no ID was found")
      self._insert_report(report)

  def _update_report(self, report: sentiment_report.SentimentReportEntity):
    query: str = """
        UPDATE SentimentReports
        SET
            sources = %s,
            dataOutputs = %s,
            topic = %s,
            dateRangeStart = %s,
            dateRangeEnd = %s,
            status = %s,
            createdOn = %s,
            lastUpdatedOn = %s,
            includeJustifications = %s
        WHERE
            reportId = %s
    """

    sources_as_names = [source.name for source in report.sources]
    data_outputs_as_names = [output.name for output in report.data_outputs]

    update_params = (
        sources_as_names,
        data_outputs_as_names,
        report.topic,
        report.start_time,
        report.end_time,
        report.status,
        report.created,
        report.last_updated,
        report.include_justifications,
        report.entity_id,
    )
    self._postgres_client.update_row(query, update_params)

    if report.datasets:
      logger.debug(
          "Persisting %d datasets for report %s", len(report.datasets),
          report.entity_id
      )
      self._persist_datasets(report.datasets, report.entity_id)

  def _insert_report(self, report: sentiment_report.SentimentReportEntity):
    """Inserts a new report into the database."""
    query: str = """
        INSERT INTO SentimentReports (
            sources,
            dataOutputs,
            topic,
            dateRangeStart,
            dateRangeEnd,
            includeJustifications
        ) VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING reportId;
    """
    sources_as_names = [source.name for source in report.sources]
    data_outputs_as_names = [output.name for output in report.data_outputs]

    params = (
        sources_as_names,
        data_outputs_as_names,
        report.topic,
        report.start_time,
        report.end_time,
        report.include_justifications,
    )

    new_id = self._postgres_client.insert_row(query, params)
    report.entity_id = new_id

    if report.datasets:
      self._persist_datasets(report.datasets, new_id)

  def _persist_datasets(
      self, datasets: list[report_msg.SentimentReportDataset], report_id: str
  ):
    """Persists the datasets associated with a sentiment report.

    Args:
      datasets: The list of datasets to persist.
      report_id: The ID of the report these datasets belong to.
    """
    # First, delete existing datasets for this report
    delete_query = """
        DELETE FROM SentimentReportDatasets
        WHERE reportId = %s;
    """
    self._postgres_client.delete_rows(delete_query, (report_id,))

    # Then, insert the new/updated datasets
    insert_query = """
        INSERT INTO SentimentReportDatasets (
            reportId,
            source,
            dataOutput,
            outputUri
        ) VALUES (%s, %s, %s, %s)
        RETURNING reportDatasetId;
    """
    for dataset in datasets:
      params = (
          report_id, dataset.source.name, dataset.data_output.name,
          dataset.dataset_uri
      )
      self._postgres_client.insert_row(insert_query, params)

  def _create_sentiment_report_from_row(
      self, row: tuple[Any, ...]
  ) -> sentiment_report.SentimentReportEntity:
    """Creates a SentimentReport message from a database row.

    Args:
      row: A tuple representing a row from the SentimentReports table.

    Returns:
      A SentimentReport message populated with data from the row.
    """
    if not row:
      raise ValueError("Provided row was None or empty.")

    datasets = self._get_report_datasets(row[REPORTID_COL_INDEX])

    return sentiment_report.SentimentReportEntity(
        report_id=row[REPORTID_COL_INDEX],
        status=row[STATUS_COL_INDEX],
        sources=[
            common_msg.SocialMediaSource[source]
            for source in row[SOURCES_COL_INDEX]
        ],
        data_outputs=[
            common_msg.SentimentDataType[output]
            for output in row[DATAOUTPUTS_COL_INDEX]
        ],
        topic=row[TOPIC_COL_INDEX],
        start_time=row[DATERANGESTART_COL_INDEX],
        end_time=row[DATERANGEEND_COL_INDEX],
        created=row[CREATEDON_COL_INDEX],
        last_updated=row[LASTUPDATEDON_COL_INDEX],
        include_justifications=row[INCLUDEJUSTIFICATIONS_COL_INDEX],
        relevance_threshold=row[RELEVANCETHRESHOLD_COL_INDEX],
        datasets=datasets,
    )

  def _get_report_datasets(
      self, report_id: str
  ) -> list[report_msg.SentimentReportDataset]:
    """Retrieves the datasets associated with a given report ID.

    Args:
      report_id: The report ID to retrieve datasets for.

    Returns:
      A list of datasets associated with the report, or an empty list if none
      where found.
    """

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
        ) for row in rows
    ]
