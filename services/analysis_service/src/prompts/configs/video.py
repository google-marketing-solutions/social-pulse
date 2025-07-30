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
    video itself in your response.
    """


PROVIDE_JUSTIFICATION_STANZA = """  In addition, extract up to 3 quotes from the
  video that justify the sentiment score you provided.  Make sure the quotes
  are actually said in the video.
  """


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


VIDEO_SHARE_OF_VOICE_SCORE_PROMPT_TEMPLATE = prompt_string = """Ignoring any
  previous questions and answers, examine the video and identify what
  products/brands are mentioned with respect to the following topic:

  ${topic}

  For each product or brand that you identify, analyze the video for them and
  generate an overall sentiment score of the video towards that product or
  brand.  Provide 1 of the following scores based on the provided guidance:
    1. Extremeley negative (score = -1.0)
    2. Negative (score = -0.5)
    3. Partially negative (score = -0.2)
    4. Nuetral (score = 0.0)
    5. Partially positive (score = 0.2)
    6. Positive (score = 0.5)
    7. Extremely positive (score = 1.0)

  In addition, generate a weight score, that represents how much the
  product/brand is mentioned in the video compared to the other brands/products.
  The weights of all of the products, when summed up, should be 100.

  In addition, generate a relevance score, that represents how revelevant the
  video is towards the product or brand. Where 1 means the product/brand
  isn't directly related to the topic, and 100 means the product/brand is
  tightly related to the topic.

  In addition, generate a short summary of 3 to 4 sentences that summarize the
  video, hitting on what specific points the creator brings up about the
  products/brands.

   When analyzing the video, keep the following in mind:
    1.  Only reference information in the video itself in your response.
    2.  Ignore any product or brand that's mentioned but is not relevant to the
        provided topic.  For example, ignore any brand or product that's
        mentioned as a sponsor.
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
    scoring_prompt = string.Template(VIDEO_SENTIMENT_SCORE_PROMPT_TEMPLATE)
    brand_or_product = self._workflow_exec.topic

    return scoring_prompt.substitute(brand_or_product=brand_or_product)

  def get_response_schema(self) -> str:
    return core.SentimentResponseSchemaBuilder().build()

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
    return scoring_prompt.substitute(topic=topic)

  def get_response_schema(self) -> str:
    return core.SentimentResponseSchemaBuilder().add_property(
        core.SHARE_OF_VOICE_WEIGHT_RESPONSE_SCHEMA_MIXIN
    ).build()

  def get_file_data(self, row):
    return [("video/*", row["videoUrl"])]
