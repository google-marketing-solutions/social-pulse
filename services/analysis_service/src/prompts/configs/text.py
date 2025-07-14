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

TEXT_SENTIMENT_SCORE_PROMPT_TEMPLATE = """Ignoring any previous questions and
  answers, examine the video comment and identify if it references
  any of the following products or brands for you to analyze:

  ${brand_or_product}

  For each product or brand that you identify, analyze the video comment for
  them and generate an overall sentiment score of the video comment towards
  that product or brand, where -1.0 represents an extremely negative
  sentiment, 1.0 represents an extremely positive sentiment, and 0 represents
  a neutral sentiment.

  In addition, generate a relevance score, that represents how revelevant the
  video comment is towards the product or brand. Where 0 means the
  video comment doesn't allude to product or brand at all, and 100 means
  the video comment is exclusively about the product or brand. When
  generating a score, use the following guidelines:

  1) If the comment is comprised of all emojis, it's considered not relevant.
  2) If the comment is simply praising the video creator for creating a good
    video (ie, "Great video! I really liked it!"), than it's considered not
    relevant.
  3) If the comment specifically mentions the product or brand, or
    if it mentions a feature of the product (ie, "I really like how you can
    use the widget to search for X"), then it's considered very relevant.

  To help you analyze the video comment, here's a summary of the
  video that the comments were posted to:

  ${video_summary}

  Finally, if for whatever reason you can't provide any analysis, like if
  there's too little text in the comment, or a completely blank comment,
  then return a response with a sentiment score of 0.0, a relevance score
  of 0, and "N/A" for the product or brand.

  Here's the video comment to analyze:

  ${video_comment}
  """


class BasicSentimentScoreFromCommentPromptConfig(core.PromptConfig):
  """Configuration for generating text analysis prompts."""

  def get_input_columns(self) -> list[str]:
    return [
        "commentId",
        "videoId",
        "authorId",
        "videoSummary",
        "text",
        "parentId",
    ]

  def get_system_instruction(self) -> str:
    return TEXT_EXTRACTION_SYSTEM_INSTRUCTION

  def generate_llm_prompt(self, row: pd.Series) -> str:
    scoring_prompt = string.Template(TEXT_SENTIMENT_SCORE_PROMPT_TEMPLATE)
    brand_or_product = self._workflow_exec.topic

    return scoring_prompt.substitute(
        brand_or_product=brand_or_product,
        video_summary=row["videoSummary"],
        video_comment=row["text"]
    )

  def get_response_schema(self) -> str:
    return core.SentimentResponseSchemaBuilder().build()

  def get_file_data(self, row: pd.Series) -> list[tuple[str, str]] | None:
    return None
