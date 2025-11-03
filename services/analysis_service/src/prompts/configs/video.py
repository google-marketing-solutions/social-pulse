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
"""Constants and classes for creating video based content prompts."""
import string

import pandas as pd
from prompts.configs import core


VIDEO_EXTRACTION_SYSTEM_INSTRUCTION = """
  Act as an expert research analyst and content strategist. Your goal is to
  deconstruct the provided YouTube video to extract its fundamental components,
  core message, and strategic elements.

  When deconstructuring a video, look through all frames of provided videos,
  start to finish, extracting out the pieces necessary to get the components and
  core message.

  Finally,  you will use the video analysis to respond to user prompts. Only
  reference information in the video itself in your response - **DO NOT
  REFERENCE ANY INFORMATION FROM ADDITIONAL SOURCES (E.G., GOOGLE SEARCH).
  """


VIDEO_SENTIMENT_SCORE_PROMPT_TEMPLATE = """
  **Product, Brand, or Feature to Analyze (Target Entity):** ${brand_or_product}
  **Video to analyze:  ${video_url}**
  ---

  ## **CRITICAL OUTPUT REQUIREMENT**

  Your entire response **MUST** be a single, raw JSON object
  that validates against the `responseSchema`. Do not include
  any text, backticks, or explanations before or after the JSON.
  Your entire response must start with `{` and end with `}`.

  ---

  ## **Instructions for JSON Generation**

  Follow these steps *sequentially* to generate the JSON output.

  ### **Step 1: Generate `summary` (string)**

  1.  Watch and analyze the provided video in its entirety, including what is
      said, any text that is displayed, and any additional visuals.
  2.  Generate a neutral, factual summary of the video's content.  If any brands
      or products are mentioned, please include them in your summary.
  3.  Limit the summary to 4 to 5 sentences, making sure to **prioritize
      being succinct** over being complete.

  ### **Step 2: Generate `relevanceScore` (number)**

  1.  Compare the **Internal Summary** from Step 1 to the
      **Target Entity** (`${brand_or_product}`).
  2.  Assign a score from 1-100. (100 = primary focus,
      50 = discussed significantly, 1 = not relevant).
  3.  Place this number into the `relevanceScore` field.

  ### **Step 3: Generate `sentiments` (array)**

  **Conditional Logic:**
  * **If `relevanceScore` < 50:** The `sentiments` array
      **must** be empty (`[]`).
  * **If `relevanceScore` >= 50:**
      1.  **Search for Target Entity:** Actively search the video for
          mentions of the **Target Entity** (`${brand_or_product}`).
      2.  If the **Target Entity** is *not* found as a relevant
          discussion point, the `sentiments` array **must**
          be empty (`[]`).
      3.  If the **Target Entity** *is* found:
          * Create a single JSON object for the **Target Entity**
              and add it to the `sentiments` array.
          * This object must have the following properties:
              * **`productOrBrand` (string):** The exact **Target Entity** you
                were asked to analyze.
              * **`sentimentScore` (string - enumeration):**  Examine the video
                content to determine the sentiment of the video towards the
                **Target Entity**.  Use one of the enumerated values below to
                represent the sentiment:
                * Extremely Positive ("EXTREME_POSITIVE")
                * Positive ("POSITIVE")
                * Partially Positive  ("PARTIAL_POSITIVE")
                * Neutral  ("neutral")
                * Partially Negative  ("PARTIAL_NEGATIVE")
                * Negative  ("NEGATIVE")
                * Extremely Negative  ("EXTREME_NEGATIVE")
  """


PROVIDE_JUSTIFICATION_STANZA = """
              * **`justifications` (array of objects):** This field provides
                the evidence for the `sentimentScore`.
                  1.  Find 1 to 3 **verbatim quotes** from the video that
                      are the primary evidence for the assigned `sentimentScore`.
                  2.  For each quote, identify its start time in the video.
                  3.  Create a JSON object for each quote with two keys:
                      * **`quote` (string):** The exact, verbatim quote.
                        Do not paraphrase.
                      * **`timestamp` (string):** The timestamp where the
                        quote begins, in "MM:SS" or "HH:MM:SS" format
                        (e.g., "00:38" or "01:05:22").
                  4.  Add these objects to the `justifications` array.
  """


VIDEO_SHARE_OF_VOICE_SCORE_PROMPT_TEMPLATE = """
  **Topic for Analysis:** "${topic}"
  **Video to Analayze:  ${video_url}
  ---

  ### **CRITICAL OUTPUT REQUIREMENT**

  Your entire response **MUST** be a single, raw JSON object
  that validates against the `responseSchema`. Do not include
  any text, backticks, or explanations before or after the JSON.
  Your entire response must start with `{` and end with `}`.

  ---

  ### **Instructions for JSON Generation**

  Follow these steps *sequentially* to generate the JSON output.

  ### **Step 1: Generate `summary` (string)**

  1.  Watch and analyze the provided video in its entirety, including what is
      said, any text that is displayed, and any additional visuals.
  2.  Generate a neutral, factual summary of the video's content.  If any brands
      or products are mentioned, please include them in your summary.
  3.  Limit the summary to 4 to 5 sentences, making sure to **prioritize
      being succinct** over being complete.

  ### **Step 2: Generate `relevanceScore` (number)**

  1.  Compare the **Internal Summary** from Step 1 to the
      "Topic for Analysis."
  2.  Assign a score from 1-100 based on the following rules:
      * **100:** The video's *primary focus* is a perfect
          match for all parts of the topic.
      * **50:** The video is partially related (e.g., it
          discusses "AI" in general but not "AI Native ERP").
      * **1:** The video is completely unrelated to the topic.
  3.  Place this number into the `relevanceScore` field.

  ### **Step 3: Generate `sentiments` (array)**

  **Conditional Logic:**
  * **If `relevanceScore` < 50:** The `sentiments` array
      **must** be empty (`[]`).
  * **If `relevanceScore` >= 50:** Populate the array by
      following these sub-steps:

      1.  **Identify Mentions:** List all products/brands
          mentioned in the video.
      2.  **Filter by Relevance:** From that list, remove any brand
          that is not relevant to the "Topic for Analysis"
          (e.g., channel sponsors, unrelated software, etc.).
      3.  **Consolidate:** If one brand has multiple products
          (e.g., "Acme Zoom" and "Acme Fusion"), consolidate them
          under the single brand "Acme".
      4.  **Create Objects:** For each final, relevant brand, create
          a JSON object and add it to the `sentiments` array.
          This object must have the following three properties:

          * **`productOrBrand` (string):** The name of the
              consolidated brand.
          * **`sentimentScore` (string - enumeration):**
                First, determine the sentiment from this list:
          * **`sentimentScore` (string - enumeration):**  Examine the video
                content to determine the OVERALL sentiment of the video towards
                the **Target Entity**, and choose a SINGLE value from below
                to represent the overall sentiment.  Use one of the enumerated
                values below:
                * Extremely Positive ("EXTREME_POSITIVE")
                * Positive ("POSITIVE")
                * Partially Positive  ("PARTIAL_POSITIVE")
                * neutral  ("neutral")
                * Partially Negative  ("PARTIAL_NEGATIVE")
                * Negative  ("NEGATIVE")
                * Extremely Negative  ("EXTREME_NEGATIVE")
          * **`weight` (number):** A percentage (1-100)
              representing how much this brand was discussed
              *compared to the other relevant brands*. The sum of
              all `weight` scores must equal 100. (If only one
              brand is relevant, its weight is 100).
  """


class BasicSentimentScoreFromVideoPromptConfig(core.PromptConfig):
  """Configuration for generating video sentiment analysis prompts."""

  def get_input_columns(self) -> list[str]:
    return [
        "videoId",
        "videoTitle",
        "videoDescription",
        "videoUrl",
        "channelId",
        "channelTitle",
        "publishedAt",
    ]

  def get_system_instruction(self) -> str:
    return VIDEO_EXTRACTION_SYSTEM_INSTRUCTION

  def generate_llm_prompt(self, row: pd.Series) -> str:
    template_string = VIDEO_SENTIMENT_SCORE_PROMPT_TEMPLATE
    if self._workflow_exec.include_justifications:
      template_string += PROVIDE_JUSTIFICATION_STANZA

    brand_or_product = self._workflow_exec.topic
    video_url = row["videoUrl"]

    scoring_prompt = string.Template(template_string)
    return scoring_prompt.substitute(
        brand_or_product=brand_or_product, video_url=video_url
    )

  def get_response_schema(self) -> str:
    schema_builder = core.SentimentResponseSchemaBuilder()

    if (self._workflow_exec.include_justifications):
      schema_builder.add_property(core.JUSTIFICATION_RESPONSE_SCHEMA_MIXIN)

    return schema_builder.build()

  def get_file_data(self, row: pd.Series) -> list[tuple[str, str]] | None:
    return [("video/*", row["videoUrl"])]


class ShareOfVoiceSentimentScoresFromVideoPromptConfig(core.PromptConfig):
  """Configuration for generating video SoV analysis prompts."""

  def get_input_columns(self) -> list[str]:
    return [
        "videoId",
        "videoTitle",
        "videoDescription",
        "videoUrl",
        "channelId",
        "channelTitle",
        "publishedAt",
    ]

  def get_system_instruction(self) -> str:
    return VIDEO_EXTRACTION_SYSTEM_INSTRUCTION

  def generate_llm_prompt(self, row: pd.Series) -> str:
    scoring_prompt = string.Template(VIDEO_SHARE_OF_VOICE_SCORE_PROMPT_TEMPLATE)
    topic = self._workflow_exec.topic
    video_url = row["videoUrl"]

    return scoring_prompt.substitute(topic=topic, video_url=video_url)

  def get_response_schema(self) -> str:
    return (
        core.SentimentResponseSchemaBuilder()
        .add_property(core.SHARE_OF_VOICE_WEIGHT_RESPONSE_SCHEMA_MIXIN)
        .build()
    )

  def get_file_data(self, row):
    return [("video/*", row["videoUrl"])]
