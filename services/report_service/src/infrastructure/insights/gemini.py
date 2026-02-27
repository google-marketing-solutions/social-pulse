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

from domain.ports.insights import InsightsProvider
from socialpulse_common.gemini import GeminiPromptClient


logger = logging.getLogger(__name__)

GEMINI_MODEL_NAME = "gemini-3-pro-preview"
GEMINI_MODEL_LOCATION = "global"


class GeminiInsightsProvider(InsightsProvider):
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
            "identifying key trending topics from social listening reports."
        )
        prompt = f"""
          Task: Analyze the social listening report data and identify 2-3 of
          the most significant topics discussed in the
          report justifications. Ensure these topics are distinct and
          represent different aspects of the report data. They should be
          more about topics and discussed and less about the metrics and
          spikes themselves. Justifications should be speicific video or
          comment quote examples from the report context. Focus EXCLUSIVELY
          on 'views' as the primary metric for these base insights; ignore
          likes/comments here.

          Rules:
          - Keep findings snappy and concise for a UI card format. The
            'description' must be 1-2 short sentences maximum.
          - If 1 or 2 specific videos or channels are the primary reason for a
            trend, you MUST explicitly call them out by name in the description.
          - For the "justifications" array, you MUST use exact user quotes
            from the 'sentiments.justifications.quote' data in the report.
            Do not just return the justification category.
          - Format your response exactly as valid JSON matching the schema
            below. Do not include markdown code blocks.

          Output Format:
          {{
            "top_trends": [
              {{
                "trend_title": "string",
                "description": "string (See Rules for constraints)",
                "justifications": [
                  "string (Exact user quote)",
                  "string (Exact user quote)"
                ]
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
          Task: Analyze the social listening report data to identify up to 2
          significant spikes in activity or sentiment. Focus EXCLUSIVELY on
          'views' to identify these spikes.

          Rules:
          - Weigh specific video justifications and content evidence heavily
            over general macroeconomic events.
          - Keep the 'cause_analysis' snappy and concise for a UI card (max
            1-2 short sentences).
          - If 1 or 2 specific videos or channels are the main driver of the
            spike, explicitly call them out by name in the 'cause_analysis'.
          - For 'primary_video_evidence', you MUST use exact user quotes from
            the 'sentiments.justifications.quote' data and specific video
            titles. Do not just return the justification category.
          - If no significant spikes exist in the data, return an empty array.
          - Format your response exactly as valid JSON matching the schema
            below. Do not include markdown code blocks.

          Output Format:
          {{
            "spikes": [
              {{
                "spike_topic": "string",
                "cause_analysis": "string (See Rules for constraints)",
                "primary_video_evidence": [
                  "string (Exact user quote and/or video title)"
                ],
                "spike_magnitude": "string ('high', 'medium', 'low')",
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
            "You are a quick and helpful Social Analyst assistant answering "
            "questions about a social listening report. While the dashboard "
            "focuses on views, you should actively help users explore other "
            "metrics like likes and comments if they ask."
        )

        # Format chat history for the prompt
        formatted_history = "\n".join(
            [
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in chat_history
            ]
        )

        prompt = f"""
          Task: Answer the user's query using ONLY the provided Report
          Context and Chat History.

          Rules:
          - Keep answers snappy, conversational, and concise for a chat UI.
          - If the user asks about metrics beyond views (like likes, comments),
            provide detailed answers based on the report data.
          - Ground justifications in exact user quotes from the
            'sentiments.justifications.quote' data. Do not just cite a category.
          - If 1 or 2 specific videos/channels drive a trend or spike being
            discussed, call them out explicitly by name in the answer.
          - If the user asks for a video, provide the title and channel.
          - If the user asks for a channel, provide the name and link.
          - If the answer cannot be found in the Report Context, politely
            state that you do not have that information.

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
                temperature=0.7,
                tools=[{"code_execution": {}}],
            )
            return response.text
        except Exception as e:
            logger.error("Gemini chat generation failed: %s", e)
            raise

    def _generate_json_content(
        self, system_instruction: str, prompt: str
    ) -> tuple[dict[str, Any], str]:
        """Helper to generate content and parse JSON response.

        Args:
            system_instruction: The system instruction for the model.
            prompt: The user query or prompt.

        Returns:
            A tuple containing parsed JSON of the insights and raw string
            response.

        Raises:
            Exception: If content parsing or generation fails.
        """
        try:
            response = self._client.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                system_instruction=system_instruction,
                temperature=0.1,
                response_mime_type="application/json",
                use_thinking=True,
                tools=[{"code_execution": {}}],
            )
            return json.loads(response.text), response.text
        except Exception as e:
            logger.error("Gemini JSON generation failed: %s", e)
            raise
