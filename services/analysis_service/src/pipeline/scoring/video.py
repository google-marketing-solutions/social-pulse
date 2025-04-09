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
"""Module for setting up a video sentiment scoring analysis."""


import copy
import string

import pandas as pd
from pipeline import core
from pipeline.scoring import constants
from prompts import generator
from socialpulse_common.messages import workflow_execution_pb2 as wfe


VIDEO_EXTRACTION_SYSTEM_INSTRUCTION = """You are a video analyst that carefully
    looks through all frames of provided videos, extracting out the pieces
    necessary to respond to user prompts. Make sure to look through and listen
    to the whole video, start to finish.  Only reference information in the
    video itself in your response."""


SENTIMENT_SCORE_PROMPT_TEMPLATE = """Ignoring any previous questions and
    answers, examine the video and  identify if it contains any of the
    following products or brands for you to analyze:

    ${topic_list}

    For each product or brand that you identify, analyze the video for
    them and generate an overall sentiment score of the video towards
    that product or brand, where -1.0 represents an extremely negative
    sentiment, 1.0 represents an extremely positive sentiment, and 0 represents
    a neutral sentiment.

    In addition, generate a relevance score, that represents how revelevant the
    video is towards the product or brand.  Where 0 means the
    video doesn't mentiond the product or brand at all, and 100 means
    the video is exclusively about the product or brand.

    In addition, generate a short summary of 3 to 4 sentences that summarize the
    video, hitting on what specific points the creator brings up about the
    product or brand.
    """


JUSTIFICATION_PROMPT_CLAUSE = """In addition, pull out up to 3 quotes that are
    positive about the product or brand, and up to 3 quotes that are negative
    about the product or brand.

    Make sure to only include quotes from the video, and only quotes
    about the products or brands you're analyzing.  Finally generate 1 row per
    product or brand that you identify and analyze."""


class AttachBatchVideoAnalysisRequestStep(core.AnalysisStep):
  """Generates and attaches a batch LLM request to the social content data.

  Uses report information and the social content data to generate a batch
  LLM prediction request, and then attaches it to the social content data in
  a column called "request".
  """

  def execute(self, data: pd.DataFrame) -> pd.DataFrame:
    """Attaches a batch request for generating a score and justifications.

    Args:
      data: The input data for the analysis step.

    Returns:
      The output data after the sentiment analysis step has been executed.
    """
    data[constants.LLM_REQUEST_COL_NAME] = data.apply(
        self._attach_request_fn,
        axis=1
    )
    return data

  def _attach_request_fn(
      self,
      row: pd.Series,
  ) -> str:
    """Function for generating the batch prediction request.

    This method generates a prompt for the LLM based on the content of the row
    and the report parameters. It then creates an LLM request with the prompt,
    system instruction, response schema, and other parameters.

    Args:
      row: A row of social content data.

    Returns:
      A string representing the LLM request.
    """
    response_schema = copy.deepcopy(constants.BASE_SENTIMENT_RESPONSE_SCHEMA)
    if (
        wfe.SentimentDataType.SENTIMENT_DATA_TYPE_JUSTIFICATION
        in self.execution_params.data_outputs
    ):
      response_schema["items"]["properties"].update(
          constants.JUSTIFICATION_RESPONSE_SCHEMA
      )

    prompt_generator: generator.LlmPromptGenerator = (
        generator.LlmPromptGenerator(
        ).with_prompt(
            self._generate_base_prompt(row)
        ).with_system_instruction(
            VIDEO_EXTRACTION_SYSTEM_INSTRUCTION
        ).with_response_schema(
            response_schema
        ).with_temperature(
            0.5
        ).with_response_mime_type(
            "application/json"
        )
    )

    prompt_generator.with_file_data([
        ("video/*", row["videoUrl"])
    ])

    return prompt_generator.build()

  def _generate_base_prompt(self, content: pd.Series) -> str:
    """Generates the base prompt for the LLM.

    Args:
      content: A row of social content data.

    Returns:
      The base prompt for the LLM.
    """
    scoring_prompt = string.Template(SENTIMENT_SCORE_PROMPT_TEMPLATE)
    prompt = scoring_prompt.substitute(
        topic_list=self.execution_params.topic
    )

    if (
        wfe.SentimentDataType.SENTIMENT_DATA_TYPE_JUSTIFICATION
        in self.execution_params.data_outputs
    ):
      prompt += JUSTIFICATION_PROMPT_CLAUSE

    return prompt
