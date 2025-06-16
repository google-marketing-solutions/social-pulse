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

"""Module providing concrete implementation for a generative ai client using vertexai."""

import logging
import google.generativeai as genai
import vertexai


# Initialize logging
logger = logging.getLogger(__name__)


class GeminiSentimentAnalyzer:
  """Analyzes content using Vertex AI's Generative Model."""

  def __init__(self, api_key: str, project_id: str, project_location: str):
    """Initializes the GeminiSentimentAnalyzer with a Vertex AI API client and a Vertex AI model.

    Args:
        api_key (str): Your Vertex AI API key.
        project_id (str): Your GCP project ID
        project_location (str): Your GCP project location
    """
    if not api_key:
      logger.error("Vertex AI API key is required.")
      raise ValueError("Vertex AI API key is required.")
    self._api_key = api_key

    if not project_id:
      logger.error("GCP project ID is required.")
      raise ValueError("GCP project ID is required.")
    self._project_id = project_id

    if not project_location:
      logger.error("GCP project location is required.")
      raise ValueError("GCP project location is required.")
    self._project_location = project_location

    try:
      vertexai.init(project=project_id, location=project_location)
      genai.configure(api_key=api_key)
      gemini_model = "models/gemini-2.5-flash-preview-04-17"
      self._model = genai.GenerativeModel(model_name=gemini_model)

      logger.info("GeminiSentimentAnalyzer initialized.")
    except Exception as e:  # pylint: disable=broad-exception-caught
      logger.exception("Failed to initialize genai model: %s", e)
      raise

  def analyze_content_with_gemini(self, prompt: str) -> dict[str]:
    """Analyzes content using Vertex AI's generate_content API.

    Args:
        prompt (str): Type of content ("online video", "video comment",
        "review post").

    Returns:
        Any: The parsed response from the Vertex AI generate_content API,
        or None if an error occurs.
    """

    try:
      response = self._model.generate_content(prompt)
      return response.text

    except Exception as e:  # pylint: disable=broad-exception-caught
      logger.error("Error calling Vertex AI generate_content API: %s", e)
      return {"error": f"Failed to get analysis from Vertex AI: {e}"}
