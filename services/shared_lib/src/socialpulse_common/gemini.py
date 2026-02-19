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

"""Module providing a generic Gemini prompt client."""

import logging
from typing import Any
from google import genai
from google.genai import types

# Initialize logging
logger = logging.getLogger(__name__)


class GeminiPromptClient:
    """Generic client for generating content using Google's GenAI SDK."""

    def __init__(
        self, api_key: str, project_id: str, location: str = "global"
    ):
        """Initializes the GeminiPromptClient with a GenAI client.

        Args:
            api_key (str): Your GenAI API key.
            project_id (str): Your GCP project ID.
            location (str): The GCP location for the model.
                Defaults to "global".
        """
        if not api_key:
            logger.error("API key is required.")
            raise ValueError("API key is required.")
        self._api_key = api_key

        if not project_id:
            logger.error("GCP project ID is required.")
            raise ValueError("GCP project ID is required.")
        self._project_id = project_id
        self._location = location

        try:
            self._client = genai.Client(
                vertexai=True,
                project=project_id,
                location=location,
            )
            logger.info("GeminiPromptClient initialized.")
        except Exception as e:
            logger.error("Failed to initialize Gemini client: %s", e)
            raise

    def generate_content(
        self,
        model: str,
        contents: str,
        system_instruction: str | None = None,
        temperature: float | None = None,
        response_mime_type: str | None = None,
        use_thinking: bool = False,
    ) -> Any:
        """Generates content from the Gemini model.

        Args:
            model (str): The name of the Gemini model to use.
            contents (str): The prompt contents to send to the model.
            system_instruction (str | None): Optional system instruction
                to guide the model.
            temperature (float | None): Optional temperature setting.
            response_mime_type (str | None): Optional MIME type for
                the expected response (e.g. 'application/json').
            use_thinking (bool): Whether to enable high-level thinking.

        Returns:
            Any: The response object from the GenAI client.
        """
        kwargs = {}
        if system_instruction is not None:
            kwargs["system_instruction"] = system_instruction
        if temperature is not None:
            kwargs["temperature"] = temperature
        if response_mime_type is not None:
            kwargs["response_mime_type"] = response_mime_type
        if use_thinking:
            kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_level=types.ThinkingLevel.HIGH
            )

        config = types.GenerateContentConfig(**kwargs) if kwargs else None

        try:
            response = self._client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            return response
        except Exception as e:
            logger.error("Gemini generation failed: %s", e)
            raise
