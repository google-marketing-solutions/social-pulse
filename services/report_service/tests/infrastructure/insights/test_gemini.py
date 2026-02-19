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
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Unit tests for the GeminiInsightsProvider class."""

import json
import unittest
from unittest import mock
from services.report_service.src.infrastructure.insights.gemini import (
    GeminiInsightsProvider,
)


class TestGeminiInsightsProvider(unittest.TestCase):
    """Test suite for the GeminiInsightsProvider class."""

    def setUp(self):
        super().setUp()
        self.api_key = "test_api_key"
        self.project_id = "test_project_id"
        self.report_context = "Sample report context"

    @mock.patch(
        "services.report_service.src.infrastructure.insights.gemini"
        ".GeminiPromptClient"
    )
    def test_initialization_success(self, mock_client_class):
        """Test successful initialization of GeminiInsightsProvider."""
        provider = GeminiInsightsProvider(self.api_key, self.project_id)
        mock_client_class.assert_called_once_with(
            api_key=self.api_key,
            project_id=self.project_id,
            location="global"
        )
        # pylint: disable=protected-access
        self.assertIsNotNone(provider._client)

    @mock.patch(
        "services.report_service.src.infrastructure.insights.gemini"
        ".GeminiPromptClient"
    )
    def test_generate_base_insights_success(self, mock_client_class):
        """Test successful generation of base insights."""
        mock_client_instance = mock_client_class.return_value

        expected_response = {
            "top_trends": [
                {
                    "trend_title": "Trend 1",
                    "description": "Description 1",
                    "justifications": ["Justification 1"]
                }
            ]
        }
        mock_response = mock.MagicMock()
        mock_response.text = json.dumps(expected_response)
        mock_client_instance.generate_content.return_value = mock_response

        provider = GeminiInsightsProvider(self.api_key, self.project_id)
        result_json, result_raw = provider.generate_base_insights(
            self.report_context
        )

        self.assertEqual(result_json, expected_response)
        self.assertEqual(result_raw, mock_response.text)
        mock_client_instance.generate_content.assert_called_once()
        _, kwargs = mock_client_instance.generate_content.call_args
        self.assertEqual(kwargs.get("response_mime_type"), "application/json")
        self.assertTrue(kwargs.get("use_thinking"))

    @mock.patch(
        "services.report_service.src.infrastructure.insights.gemini"
        ".GeminiPromptClient"
    )
    def test_generate_spike_analysis_success(self, mock_client_class):
        """Test successful generation of spike analysis."""
        mock_client_instance = mock_client_class.return_value

        expected_response = {
            "spikes": [
                {
                    "spike_topic": "Spike 1",
                    "cause_analysis": "Analysis 1",
                    "primary_video_evidence": ["Video 1"],
                    "spike_magnitude": "high",
                    "spike_trend": "increasing",
                    "spike_month": "2026-02"
                }
            ]
        }
        mock_response = mock.MagicMock()
        mock_response.text = json.dumps(expected_response)
        mock_client_instance.generate_content.return_value = mock_response

        provider = GeminiInsightsProvider(self.api_key, self.project_id)
        result_json, result_raw = provider.generate_spike_analysis(
            self.report_context
        )

        self.assertEqual(result_json, expected_response)
        self.assertEqual(result_raw, mock_response.text)

    @mock.patch(
        "services.report_service.src.infrastructure.insights.gemini"
        ".GeminiPromptClient"
    )
    def test_answer_chat_query_success(self, mock_client_class):
        """Test successful chat query answer."""
        mock_client_instance = mock_client_class.return_value

        expected_response_text = "Here is the answer."
        mock_response = mock.MagicMock()
        mock_response.text = expected_response_text
        mock_client_instance.generate_content.return_value = mock_response

        provider = GeminiInsightsProvider(self.api_key, self.project_id)
        chat_history = [{"role": "user", "content": "Question?"}]
        result = provider.answer_chat_query(
            self.report_context, chat_history, "Current query"
        )

        self.assertEqual(result, expected_response_text)

    @mock.patch(
        "services.report_service.src.infrastructure.insights.gemini"
        ".GeminiPromptClient"
    )
    def test_api_failure_handling(self, mock_client_class):
        """Test handling of API failures."""
        mock_client_instance = mock_client_class.return_value
        mock_client_instance.generate_content.side_effect = Exception(
            "API Error"
        )

        provider = GeminiInsightsProvider(self.api_key, self.project_id)

        with self.assertRaises(Exception):
            provider.generate_base_insights(self.report_context)

if __name__ == "__main__":
    unittest.main()
