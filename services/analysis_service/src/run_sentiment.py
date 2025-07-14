#!/usr/bin/env python3
#
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
"""Script to run sentiment analysis workflow via the command line."""
import argparse
import datetime
import logging

from google.protobuf import timestamp_pb2
from infrastructure.apis import vertexai
from infrastructure.apis import youtube
from infrastructure.persistence.bigquery import sentiment_data_repo
from infrastructure.persistence.postgresdb import client
from infrastructure.persistence.postgresdb import workflow_data_repo
import luigi
from socialpulse_common import config
from socialpulse_common import service
from socialpulse_common.messages import workflow_execution_pb2 as wfe
from tasks import execution
from tasks.ports import apis
from tasks.ports import persistence


settings = config.Settings()


# Set up arg descriptors and parse the args.
def valid_date(s: str) -> datetime.date:
  """Validates and converts a string to a datetime.date object.

  Args:
    s: The string to validate and convert.

  Returns:
    A datetime.date object if the string is in the format YYYY-MM-DD.

  Raises:
    argparse.ArgumentTypeError: If the string is not in the expected format.
  """
  try:
    return datetime.datetime.strptime(s, "%Y-%m-%d").date()
  except ValueError as ve:
    msg = f"Not a valid date: '{s}'. Expected format YYYY-MM-DD."
    raise argparse.ArgumentTypeError(msg) from ve


parser = argparse.ArgumentParser(
    description="Generate sentiment analysis for a given topic from a "
                "social media source."
)
parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Increase output verbosity, by setting logging to DEBUG level."
)
parser.add_argument(
    "--source",
    type=str,
    required=True,
    help="Social media content source to retrieve ('Youtube', 'Twitter', etc.)."
)
parser.add_argument(
    "--topic",
    type=str,
    required=True,
    help="Topic (brand, product or feature) to generate the "
         "sentiment analysis for."
)
parser.add_argument(
    "--output",
    type=str,
    nargs="+",
    default=["SENTIMENT_DATA_TYPE_SENTIMENT_SCORE"],
    choices=[
        value_descriptor.name
        for value_descriptor in wfe.SentimentDataType.DESCRIPTOR.values
    ],
    help="Types of sentiment data to output. Defaults to sentiment score."
)
parser.add_argument(
    "--start-date",
    required=True,
    type=valid_date,
    help="Start date of the analysis window (format: YYYY-MM-DD)."
)
parser.add_argument(
    "--end-date",
    type=valid_date,
    default=datetime.date.today(),
    help="End date of the analysis window (format: YYYY-MM-DD). "
         "Defaults to today."
)
args = parser.parse_args()


# Set up logging, using the verbose arg flag.
log_format = (
    "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
log_level = logging.DEBUG if args.verbose else logging.INFO
logging.basicConfig(level=log_level, format=log_format)
logger = logging.getLogger(__name__)


class RunSentimentAnalysis():
  """Main class to orchestrate and run the sentiment analysis workflow.

  Initializes necessary repositories and APIs, creates a workflow execution
  record, and triggers the Luigi pipeline.
  """

  def __init__(
      self,
      topic: str,
      source: str,
      output: list[str],
      start_date: datetime.date,
      end_date: datetime.date | None
  ):
    self._topic = topic
    self._source = source
    self._output = output
    self._start_date = start_date
    self._end_date = end_date

    self._register_workflow_exec_persistence_service()
    self._register_sentiment_data_repo()
    self._register_youtube_api()
    self._register_vertex_ai()

  def _register_workflow_exec_persistence_service(self) -> None:
    """Registers the workflow execution persistence service."""
    postgres_client = client.PostgresDbClient(
        host=settings.db.host,
        port=settings.db.port,
        database=settings.db.name,
        user=settings.db.username,
        password=settings.db.password
    )
    self._workflow_exec_loader_service = (
        workflow_data_repo.PostgresDbWorkflowExecutionPersistenceService(
            postgres_client
        )
    )
    service.registry.register(
        persistence.WorkflowExecutionPersistenceService,
        self._workflow_exec_loader_service
    )

  def _register_sentiment_data_repo(self) -> None:
    """Registers the sentiment data repository."""
    self._sentiment_data_repo = sentiment_data_repo.BigQuerySentimentDataRepo(
        gcp_project_id=settings.cloud.project_id,
        bq_dataset_name=settings.cloud.dataset_name
    )
    service.registry.register(
        persistence.SentimentDataRepo,
        self._sentiment_data_repo
    )

  def _register_youtube_api(self) -> None:
    """Registers the Youtube API client."""
    self._youtube_api = youtube.YoutubeApiHttpClient(
        api_key=settings.api.youtube.key,
        service_name=settings.api.youtube.service_name,
        version=settings.api.youtube.version
    )
    service.registry.register(apis.YoutubeApiClient, self._youtube_api)

  def _register_vertex_ai(self) -> None:
    """Registers the Vertex AI client."""
    self._vertex_ai = vertexai.VertexAiLlmBatchJobApiClient(
        project_id=settings.cloud.project_id,
        region=settings.cloud.region,
        bq_dataset_name=settings.cloud.dataset_name
    )
    service.registry.register(apis.LlmBatchJobApiClient, self._vertex_ai)

  def _create_workflow_exec_params(self) -> wfe.WorkflowExecutionParams:
    """Creates a WorkflowExecutionParams object from the command line arguments.

    Returns:
      A WorkflowExecutionParams object populated with the provided
      information and default values for other fields.
    """
    wfe_params = wfe.WorkflowExecutionParams()

    wfe_params.source = wfe.SocialMediaSource.Value(self._source)
    wfe_params.topic = self._topic

    for output in self._output:
      wfe_params.data_output.append(
          wfe.SentimentDataType.Value(output)
      )

    start_time_proto = timestamp_pb2.Timestamp()
    start_time_proto.FromDatetime(
        datetime.datetime.combine(self._start_date, datetime.time.min)
    )
    wfe_params.start_time.CopyFrom(start_time_proto)

    if self._end_date:
      end_time_proto = timestamp_pb2.Timestamp()
      end_time_proto.FromDatetime(
          datetime.datetime.combine(self._end_date, datetime.time.max)
      )
      wfe_params.end_time.CopyFrom(end_time_proto)

    return wfe_params

  def run(self) -> None:
    """Orchestrates and runs the sentiment analysis workflow."""
    workflow_exec = self._create_workflow_exec_params()
    workflow_exec_id = self._workflow_exec_loader_service.create_execution(
        workflow_exec
    )
    logger.info("Created workflow execution with id: %s", workflow_exec_id)

    run_result = luigi.build(
        [execution.WorkflowExecution(execution_id=workflow_exec_id)],
        detailed_summary=True,
        local_scheduler=True
    )

    logger.info("Luigi run result:\n%s", run_result.summary_text)


if __name__ == "__main__":
  print("--- Arguments Received ---")
  print(f"Verbose logging?: {args.verbose}")
  print(f"Source: {args.source}")
  print(f"Topic: {args.topic}")
  print(f"Data Output: {args.output}")
  print(f"Start Date: {args.start_date} (Type: {type(args.start_date)})")
  print(f"End Date: {args.end_date} (Type: {type(args.end_date)})")
  print("--------------------------\n")

  analysis = RunSentimentAnalysis(
      topic=args.topic,
      source=args.source,
      output=args.output,
      start_date=args.start_date,
      end_date=args.end_date
  )
  analysis.run()
