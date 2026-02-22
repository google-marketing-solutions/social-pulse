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
"""Constants and classes for creating text based content prompts."""
import string

import pandas as pd
from prompts.configs import core


TEXT_EXTRACTION_SYSTEM_INSTRUCTION = """You are a text analyst that carefully
  looks through all sentences of provided text, extracting out the pieces
  necessary to respond to user prompts. Make sure to look through and read
  the whole text sample, start to finish. Only reference information in the
  text itself in your response."""

TEXT_SENTIMENT_SCORE_PROMPT_TEMPLATE = """
  **Product, Brand, or Feature to Analyze (Target Entity):** ${brand_or_product}
  **Video summary for context:**
  ${video_summary}

  **Comment to analyze:**
  ${video_comment}

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

  1.  Read and analyze the provided comment in its entirety.
  2.  Generate a neutral, factual summary of the comment's content. If any
      brands or products are mentioned, please include them in your summary.
  3.  Limit the summary to 4 to 5 sentences, making sure to **prioritize
      being succinct** over being complete.

  ### **Step 2: Generate `relevanceScore` (number)**

  1.  Compare the **Internal Summary** from Step 1 to the
      **Target Entity** (`${brand_or_product}`).
  2.  Assign a score from 0-100 indicating how relevant the comment is to the
      **Target Entity**.
  3.  When generating a score, use the following guidelines:
      1) If the comment is comprised of all emojis, it's considered not
         relevant (0).
      2) If the comment is simply praising the video creator for creating a good
         video (ie, "Great video! I really liked it!"), then it's considered not
         relevant (0).
      3) If the comment specifically mentions the product or brand, or if it
         mentions a feature of the product (ie, "I really like how you can use
         the widget to search for X"), then it's considered very relevant (100).
  4.  Place this number into the `relevanceScore` field.

  ### **Step 3: Generate `sentiments` (array)**

  **Conditional Logic:**
  * **If `relevanceScore` < 50:** The `sentiments` array
      **must** be empty (`[]`).
  * **If `relevanceScore` >= 50:**
      1.  **Search for Target Entity:** Actively search the comment for
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
              * **`sentimentScore` (string - enumeration):**  Examine the
                comment content to determine the OVERALL sentiment of the
                comment towards the **Target Entity**, and choose a **SINGLE
                STRING** value from the list of enumerated sentiment values
                below:
                * Extremely Positive ("EXTREME_POSITIVE")
                * Positive ("POSITIVE")
                * Partially Positive  ("PARTIAL_POSITIVE")
                * neutral  ("neutral")
                * Partially Negative  ("PARTIAL_NEGATIVE")
                * Negative  ("NEGATIVE")
                * Extremely Negative  ("EXTREME_NEGATIVE")
  """


PROVIDE_JUSTIFICATION_STANZA = """
              * **`justifications` (array of objects):** This field provides
                the evidence for the `sentimentScore`.
                  1.  Find 1 to 3 **verbatim quotes** from the text that
                      are the primary evidence for the assigned
                      `sentimentScore`.
                  2.  Create a JSON object for each quote with two keys:
                      * **`quote` (string):** The exact, verbatim quote.
                        Do not paraphrase.
                  3.  Add these objects to the `justifications` array.
  """


class BasicSentimentScoreFromCommentPromptConfig(core.PromptConfig):
  """Configuration for generating text analysis prompts."""

  def get_input_columns(self) -> list[str]:
    return [
        "commentId",
        "videoId",
        "authorId",
        "summary",
        "text",
        "parentId",
    ]

  def get_system_instruction(self) -> str:
    return TEXT_EXTRACTION_SYSTEM_INSTRUCTION

  def generate_llm_prompt(self, row: pd.Series) -> str:
    scoring_prompt_str = TEXT_SENTIMENT_SCORE_PROMPT_TEMPLATE
    if self._workflow_exec.include_justifications:
      scoring_prompt_str += PROVIDE_JUSTIFICATION_STANZA

    brand_or_product = self._workflow_exec.topic
    video_summary = row["summary"]
    video_comment = row["text"]

    scoring_prompt = string.Template(scoring_prompt_str)
    return scoring_prompt.substitute(
        brand_or_product=brand_or_product,
        video_summary=video_summary,
        video_comment=video_comment
    )

  def get_response_schema(self) -> str:
    schema_builder = core.SentimentResponseSchemaBuilder()

    if (self._workflow_exec.include_justifications):
      schema_builder.add_property(core.JUSTIFICATION_RESPONSE_SCHEMA_MIXIN)

    return schema_builder.build()

  def get_file_data(self, row: pd.Series) -> list[tuple[str, str]] | None:
    return None
