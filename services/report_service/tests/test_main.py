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
"""Tests for the report service HTTP endpoints."""

import unittest
from unittest import mock

from fastapi.testclient import TestClient

# Mock dependencies before importing main to avoid DB connection issues
with mock.patch("socialpulse_common.config.Settings") as mock_settings_cls:
  mock_settings = mock_settings_cls.return_value
  mock_settings.db.host = "localhost"
  mock_settings.db.port = 5432
  mock_settings.db.name = "db"
  mock_settings.db.username = "user"
  mock_settings.db.password = "pass"
  mock_settings.cloud.workflow_runner_api_url = "http://localhost"
  mock_settings.cloud.project_id = "test-project"

  with mock.patch(
      "socialpulse_common.persistence.postgresdb_client.PostgresDbClient"
  ):
    with mock.patch(
        "socialpulse_common.persistence.bigquery_client.BigQueryClient"
    ):
      # Import main after mocks are set up
      # pylint: disable=g-import-not-at-top
      import main
      from socialpulse_common.messages import report_insight as insight_msg
      from socialpulse_common.messages import sentiment_report as report_msg


class MainApiTest(unittest.TestCase):
  """Tests for the FastAPI endpoints in main.py."""

  def setUp(self):
    super().setUp()
    self.client = TestClient(main.app)

  def test_get_insights_success(self):
    """Verifies GET /api/insights/{report_id} returns insights.

    Given a report that has been completed
    When the report insights API is called with its report ID
    Then the response contains the insights for the report
    """
    report_id = "test-report-123"
    expected_insights = [
        insight_msg.ReportInsight(
            insight_id="insight-1",
            report_id=report_id,
            insight_type=insight_msg.InsightType.TREND,
            content={"title": "Test Insight", "details": "Some content"},
        )
    ]

    with mock.patch.object(
        main.app_config.report_insights_repository,
        "get_insights_for_report",
        return_value=expected_insights,
    ):
      response = self.client.get(f"/api/insights/{report_id}")

      self.assertEqual(response.status_code, 200)
      self.assertEqual(len(response.json()), 1)
      self.assertEqual(response.json()[0]["content"]["title"], "Test Insight")

  def test_chat_about_report_success(self):
    """Verifies POST /api/insights/{report_id} performs a chat.

    Given a report that has been completed
    When the report chat API is called with a query
    Then the response contains the generated answer from the AI provider
    """
    report_id = "test-report-123"
    chat_request = {"query": "Tell me about the sentiment", "history": []}

    # Mock report entity
    mock_report = mock.Mock()
    mock_report.topic = "Test Topic"
    mock_report.status = report_msg.Status.COMPLETED
    mock_dataset = mock.Mock()
    mock_dataset.source = main.msg_common.SocialMediaSource.YOUTUBE_VIDEO
    mock_report.datasets = [mock_dataset]
    mock_report.include_justifications = True

    with mock.patch.object(
        main.app_config.sentiment_report_repository,
        "load_report",
        return_value=mock_report,
    ):
      with mock.patch.object(
          main.app_config.dataset_repository,
          "get_full_report_context",
          return_value="Mocked analysis results",
      ):
        with mock.patch.object(
            main.app_config.gemini_insights_provider,
            "answer_chat_query",
            return_value="Gemini response",
        ) as mock_chat:
          response = self.client.post(
              f"/api/insights/{report_id}", json=chat_request
          )

          self.assertEqual(response.status_code, 200)
          self.assertEqual(response.json()["response"], "Gemini response")
          mock_chat.assert_called_once()
          # Verify context contains analysis results
          context = mock_chat.call_args.kwargs["report_context"]
          self.assertIn("Mocked analysis results", context)

  def test_chat_about_report_not_found(self):
    """Verifies 404 is returned if report does not exist.

    Given a report ID that does not exist in the repository
    When the report chat API is called with that ID
    Then a 404 Not Found response is returned
    """
    report_id = "missing-report"
    chat_request = {"query": "Hello", "history": []}

    with mock.patch.object(
        main.app_config.sentiment_report_repository,
        "load_report",
        side_effect=ValueError("Report not found"),
    ):
      response = self.client.post(
          f"/api/insights/{report_id}", json=chat_request
      )

      self.assertEqual(response.status_code, 404)
      self.assertIn("Report not found", response.json()["detail"])


if __name__ == "__main__":
  unittest.main()
