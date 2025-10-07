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

from domain import sentiment_report
from domain.ports import persistence
from socialpulse_common.messages import sentiment_report as report_msg
from socialpulse_common.persistence import postgresdb_client as client


class PostgresDbSentimentReportRepo(persistence.SentimentReportRepo):
  """Implementation of a sentiment report repo in PostgresDB."""

  def __init__(self, postgres_client: client.PostgresDbClient):
    self._postgres_client = postgres_client

  def load_report(self, report_id: str):
    """Retrieves a sentiment report by its ID."""
    raise NotImplementedError

  def persist_report(self, report: sentiment_report.SentimentReportEntity):
    """Creates or updates a sentiment report.

    Persists a report, by checking if it already has a UUID.  If not, then it
    will insert the report into persistent storage.  If it does have a UUID,
    it will update the report record in storage.

    Args:
      report: The sentiment report to persist.
    """
    if report.entity_id:
      self._update_report(report)
    else:
      self._insert_report(report)

  def _update_report(self, report: sentiment_report.SentimentReportEntity):
    query: str = """
        UPDATE SentimentReportS
        SET
            sources = %s,
            dataOutputs = %s,
            topic = %s,
            dateRangeStart = %s,
            dateRangeEnd = %s,
            status = %s,
            createdOn = %s,
            lastUpdatedOn = %s
        WHERE
            reportId = %s
    """

    sources_as_names = [source.name for source in report.sources]
    data_outputs_as_names = [output.name for output in report.data_outputs]

    update_params = (sources_as_names, data_outputs_as_names, report.topic,
                     report.start_time, report.end_time, report.status,
                     report.created, report.last_updated, report.entity_id)
    self._postgres_client.update_row(query, update_params)

    if report.datasets:
      self._persist_datasets(report.datasets, report.entity_id)

  def _insert_report(self, report: sentiment_report.SentimentReportEntity):
    """"""
    query: str = """
        INSERT INTO SentimentReports (
            sources,
            dataOutputs,
            topic,
            dateRangeStart,
            dateRangeEnd
        ) VALUES (%s, %s, %s, %s, %s)
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
    )

    new_id = self._postgres_client.insert_row(query, params)
    report.entity_id = new_id

    if report.datasets:
      self._persist_datasets(report.datasets, new_id)

  def _persist_datasets(self,
                        datasets: list[report_msg.SentimentReportDataset],
                        report_id: str):
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
    params = (report_id,)
    self._postgres_client.delete_row(delete_query, params)

    # Then, insert the new/updated datasets
    insert_query = """
        INSERT INTO SentimentReportDatasets (
            reportId,
            source,
            datasetUri,
            dataOutput
        ) VALUES (%s, %s, %s, %s);
    """
    for dataset in datasets:
      params = (
          report_id,
          dataset.source.name,
          dataset.dataset_uri,
          dataset.data_output.name,
      )
      self._postgres_client.insert_row(insert_query, params)
