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

"""Module providing Gemini-powered insights provider implementation."""

import json
import logging
from typing import Any

from socialpulse_common.gemini import GeminiPromptClient

# Initialize logging
logger = logging.getLogger(__name__)

GEMINI_MODEL_NAME = "gemini-3-pro-preview"
GEMINI_MODEL_LOCATION = "global"


class GeminiInsightsProvider:
    """Implementation of InsightsProvider using Google's Gemini."""

    def __init__(self, api_key: str, project_id: str):
        """Initializes the GeminiInsightsProvider with a generic Gemini client.

        Args:
            api_key (str): Your GenAI API key.
            project_id (str): Your GCP project ID.
        """
        try:
            self._client = GeminiPromptClient(
                api_key=api_key,
                project_id=project_id,
                location=GEMINI_MODEL_LOCATION,
            )
            logger.info("GeminiInsightsProvider initialized.")
        except Exception as e:
            logger.error("Failed to initialize GeminiPromptClient: %s", e)
            raise

    def generate_base_insights(
        self, report_context: str
    ) -> tuple[dict[str, Any], str]:
        """Generates base insights (top trends) from the report context.

        Args:
            report_context (str): The full context of the report data.

        Returns:
            tuple[dict, str]: parsed JSON containing top trends
                and raw string response.
        """
        system_instruction = (
            "You are an expert Social Analyst specializing in "
            "identifying key trends from social listening reports."
        )
        prompt = f"""
          Task: Analyze the provided social listening report data and
          identify 2-3 of the most significant trends.

          Rules:
          - Base your analysis strictly on the specific justifications and
            data provided in the report context.
          - Format your response exactly as valid JSON matching the schema
            below. Do not include markdown code blocks.

          Output Format:
          {{
            "top_trends": [
              {{
                "trend_title": "string (Short, punchy title)",
                "description": "string (1-2 sentences explaining the trend)",
                "justifications": ["string", "string"]
              }}
            ]
          }}

          Report Context:
          {report_context}
        """
        return self._generate_json_content(system_instruction, prompt)

    def generate_spike_analysis(
        self, report_context: str
    ) -> tuple[dict[str, Any], str]:
        """Generates spike analysis from the report context.

        Args:
            report_context (str): The full context of the report data.

        Returns:
            tuple[dict, str]: parsed JSON containing spike analysis
                and raw string response.
        """
        system_instruction = (
            "You are an expert Social Analyst specializing in anomaly "
            "and spike detection within social media metrics."
        )
        prompt = f"""
          Task: Analyze the provided social listening report data to identify
          up to 2 significant spikes in activity or sentiment (if they exist).

          Rules:
          - When determining the root cause of a spike, you must weigh specific
            video justifications and content evidence significantly heavier
            than general macroeconomic events around the same time.
          - If no significant spikes exist in the data, return an empty array.
          - Format your response exactly as valid JSON matching the schema
            below. Do not include markdown code blocks.

          Output Format:
          {{
            "spikes": [
              {{
                "spike_topic": "string",
                "cause_analysis": "string (Explanation weighing evidence)",
                "primary_video_evidence": ["string"],
                "spike_magnitude": "string (e.g., 'high', 'medium', 'low')",
                "spike_trend": "string ('increasing', 'decreasing', 'stable')",
                "spike_month": "string (YYYY-MM)"
              }}
            ]
          }}

          Report Context:
          {report_context}
        """
        return self._generate_json_content(system_instruction, prompt)

    def answer_chat_query(
        self,
        report_context: str,
        chat_history: list[dict[str, Any]],
        query: str,
    ) -> str:
        """Answers a user chat query based on the report context and history.

        Args:
            report_context (str): The full context of the report data.
            chat_history (list[dict]): List of previous chat messages.
            query (str): The current user query.

        Returns:
            str: The conversational response.
        """
        system_instruction = (
            "You are a helpful Social Analyst assistant, answering user "
            "questions about a specific social listening report."
        )

        # Format chat history for the prompt
        formatted_history = "\n".join(
            [
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in chat_history
            ]
        )

        prompt = f"""
          Task: Answer the user's latest query using ONLY the provided Report
          Context and Chat History.

          Rules:
          - Provide a conversational, concise, and direct answer.
          - If the answer cannot be found in the Report Context, politely
            state that you do not have that information based on the report.
          - Reference specific data points from the report when answering.

          Report Context:
          {report_context}

          Chat History:
          {formatted_history}

          User Query:
          {query}

          Answer:
        """
        try:
            response = self._client.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                system_instruction=system_instruction,
                temperature=0.7,  # Slightly higher for conversation
            )
            return response.text
        except Exception as e:
            logger.error("Gemini chat generation failed: %s", e)
            raise

    def _generate_json_content(
        self, system_instruction: str, prompt: str
    ) -> tuple[dict[str, Any], str]:
        """Helper to generate content and parse JSON response."""
        try:
            response = self._client.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                system_instruction=system_instruction,
                temperature=0.1,
                response_mime_type="application/json",
                use_thinking=True,
            )
            return json.loads(response.text), response.text
        except Exception as e:
            logger.error("Gemini JSON generation failed: %s", e)
            raise
