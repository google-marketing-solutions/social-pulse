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
"""Module for setting up a video comment sentiment scoring analysis."""


import copy
import string

import pandas as pd
from pipeline import core
from pipeline.scoring import constants
from prompts import generator
from socialpulse_common.messages import workflow_execution_pb2 as wfe


TEXT_EXTRACTION_SYSTEM_INSTRUCTION = """You are a text analyst that carefully
    looks through all sentences of provided text, extracting out the pieces
    necessary to respond to user prompts. Make sure to look through and read
    the whole text sample, start to finish.  Only reference information in the
    text itself in your response."""

SENTIMENT_SCORE_PROMPT_TEMPLATE = """Ignoring any previous questions and
    answers, examine the video comment and  identify if it references
    any of the following products or brands for you to analyze:

    ${topic_list}

    For each product or brand that you identify, analyze the video comment for
    them and generate an overall sentiment score of the video comment towards
    that product or brand, where -1.0 represents an extremely negative
    sentiment, 1.0 represents an extremely positive sentiment, and 0 represents
    a neutral sentiment.

    In addition, generate a relevance score, that represents how revelevant the
    video comment is towards the product or brand.  Where 0 means the
    video comment doesn't allude to product or brand at all, and 100 means
    the video comment is exclusively about the product or brand.  For example,
    if the comment is simply praising the video creator for creating a good
    video (ie, "Great video! I really liked it!"), than the relevance score
    should be 0.  If the comment specifically mentions the product or brand, or
    if it mentions a feature of the product (ie, "I really like how you can
    use the widget to search for X"), then it should have a relevance score of
    100.

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


class AttachBatchVideoCommentAnalysisRequestStep(core.AnalysisStep):
  """Analysis step that attaches a batch request for video comment analysis.

  This step aggregates video comments and generates a request for sentiment
  analysis and justification.
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
    del response_schema["items"]["properties"]["summary"]

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
            TEXT_EXTRACTION_SYSTEM_INSTRUCTION
        ).with_response_schema(
            response_schema
        ).with_temperature(
            0.5
        ).with_response_mime_type(
            "application/json"
        )
    )

    return prompt_generator.build()

  def _generate_base_prompt(self, row: pd.Series) -> str:
    video_summary = row["videoSummary"]
    video_comment = row["text"]

    prompt_template = string.Template(SENTIMENT_SCORE_PROMPT_TEMPLATE)
    return prompt_template.substitute(
        topic_list=self.execution_params.topic,
        video_summary=video_summary,
        video_comment=video_comment
    )
