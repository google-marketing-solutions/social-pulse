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

"""Module providing concrete implementation for a generative ai client using google-genai."""

import logging
from google import genai
from google.genai import types
from tasks.ports import apis


# Initialize logging
logger = logging.getLogger(__name__)

# TODO(jmistral): Add these as init parameters, instead of constants.
GEMINI_MODEL_NAME = "gemini-3.1-pro-preview"
GEMINI_MODEL_LOCATION = "global"


class GeminiSentimentAnalyzer(apis.LlmApiClient):  # pylint: disable=too-few-public-methods
  """Analyzes content using Google's GenAI SDK."""

  def __init__(self, api_key: str, project_id: str):
    """Initializes the GeminiSentimentAnalyzer with a GenAI client.

    Args:
        api_key (str): Your GenAI API key.
        project_id (str): Your GCP project ID.
    """
    if not api_key:
      logger.error("API key is required.")
      raise ValueError("API key is required.")

    if not project_id:
      logger.error("GCP project ID is required.")
      raise ValueError("GCP project ID is required.")

    try:
      self._client = genai.Client(
          vertexai=True,
          project=project_id,
          location=GEMINI_MODEL_LOCATION,
      )
      logger.info("GeminiSentimentAnalyzer initialized.")

    except Exception as e:
      logger.error("Failed to initialize GenAI client: %s", e)
      raise

  def analyze_content(
      self, prompt: str, response_mime_type: str = "text/plain"
  ) -> str:
    """Analyzes content using Vertex AI's generate_content API.

    Args:
        prompt (str): The prompt to analyze.
        response_mime_type (str): The expected MIME type of the response.

    Returns:
        str: The response text from the Gemini API.
    """

    try:
      response = self._client.models.generate_content(
          model=GEMINI_MODEL_NAME,
          contents=prompt,
          config=types.GenerateContentConfig(
              temperature=0.1,
              response_mime_type=response_mime_type,
              thinking_config=types.ThinkingConfig(
                  thinking_level=types.ThinkingLevel.HIGH
              ),
          )
      )
      return response.text

    except Exception as e:
      logger.error("GenAI analysis failed: %s", e)
      raise
