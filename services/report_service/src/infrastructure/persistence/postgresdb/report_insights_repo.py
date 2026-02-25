"""Module for report insights repo implementations in PostgresDB."""
import json
import logging
import typing

from domain.ports import persistence
from socialpulse_common.messages import report_insight as insight_msg
from socialpulse_common.persistence import postgresdb_client as client

logger = logging.getLogger(__name__)


class PostgresDbReportInsightsRepo(persistence.ReportInsightsRepo):
  """Implementation of a report insights repo in PostgresDB."""

  def __init__(self, postgres_client: client.PostgresDbClient):
    self._postgres_client = postgres_client

  def insert_insight(
      self,
      report_id: str,
      insight_type: insight_msg.InsightType,
      content: typing.Dict[str, typing.Any],
      raw_prompt_output: str | None = None,
  ):
    """Inserts a new insight for a report.

    Args:
      report_id: The ID of the report.
      insight_type: The type of insight (TREND or SPIKE).
      content: The JSON content of the insight.
      raw_prompt_output: The raw prompt output from the LLM.
    """
    if not report_id:
      raise ValueError("Provided report_id was None or empty.")

    query: str = """
        INSERT INTO ReportInsights (
            reportId,
            insightType,
            content,
            rawPromptOutput
        ) VALUES (%s, %s, %s, %s)
        RETURNING reportInsightId;
    """
    params = (
        report_id,
        insight_type,
        json.dumps(content),
        raw_prompt_output,
    )

    new_id = self._postgres_client.insert_row(query, params)
    logger.debug("Inserted new insight with ID %s", new_id)
