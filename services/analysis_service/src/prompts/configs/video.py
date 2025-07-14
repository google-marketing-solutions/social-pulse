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


VIDEO_EXTRACTION_SYSTEM_INSTRUCTION = """You are a video analyst that carefully
    looks through all frames of provided videos, extracting out the pieces
    necessary to respond to user prompts. Make sure to look through and listen
    to the whole video, start to finish.  Only reference information in the
    video itself in your response."""


VIDEO_SENTIMENT_SCORE_PROMPT_TEMPLATE = """Ignoring any previous questions and
  answers, examine the video and identify if it contains any of the
  following products or brands for you to analyze:

  ${brand_or_product}

  For each product or brand that you identify, analyze the video for
  them and generate an overall sentiment score of the video towards
  that product or brand, where -1.0 represents an extremely negative
  sentiment, 1.0 represents an extremely positive sentiment, and 0 represents
  a neutral sentiment.

  In addition, generate a relevance score, that represents how revelevant the
  video is towards the product or brand. Where 0 means the
  video doesn't mentiond the product or brand at all, and 100 means
  the video is exclusively about the product or brand.

  In addition, generate a short summary of 3 to 4 sentences that summarize the
  video, hitting on what specific points the creator brings up about the
  product or brand.
  """


class VideoPromptConfig(core.PromptConfig):
  """Configuration for generating video analysis prompts."""

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
    scoring_prompt = string.Template(VIDEO_SENTIMENT_SCORE_PROMPT_TEMPLATE)
    brand_or_product = self._workflow_exec.topic

    return scoring_prompt.substitute(brand_or_product=brand_or_product)

  def get_response_schema(self) -> str:
    return core.BASE_SENTIMENT_RESPONSE_SCHEMA

  def get_file_data(self, row: pd.Series) -> list[tuple[str, str]] | None:
    return [("video/*", row["videoUrl"])]
