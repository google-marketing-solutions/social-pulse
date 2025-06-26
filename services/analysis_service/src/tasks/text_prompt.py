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
"""Task to generate LLM prompts to analyze text content."""
import copy
import logging
import string
import pandas as pd
from prompts import generator
from socialpulse_common import config
from tasks import constants
from tasks import core as tasks_core

settings = config.Settings()

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
    the video comment is exclusively about the product or brand.  When
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


class GenerateLlmTextAnalysisPrompts(tasks_core.SentimentTask):
  """Luigi Task to generate prompts for the Llm model.

  This task will generate prompts based on some input data (e.g., a list of
  topics, keywords, or existing text) and save them using the configured
  SentimentDataRepo.
  """

  _INPUT_COLUMNS = [
      "commentId",
      "videoId",
      "authorId",
      "videoSummary",
      "text",
      "parentId",
  ]

  _FINAL_OUTPUT_COLUMNS = [
      "prompt",
  ]

  def _validate_data(self, data: pd.DataFrame):
    """Function for validating the YouTube comments dataframe.

    This method validates the YouTube comments dataframe by checking the
    presence of the required columns.

    Args:
      data: A dataframe containing YouTube comments data.

    Returns:
      True if the validation is successful.
    """

    for column in self._INPUT_COLUMNS:
      if column not in data.columns:
        raise ValueError(
            f"[{self.task_family}] comments dataFrame missing "
            f"'{column}' column."
        )

    return True

  def run(self) -> None:
    """Executes the Llm prompt generation logic."""
    logging.info(
        "[%s] Starting GenerateLlmPrompts task for execution ID: %s",
        self.task_family,
        self.execution_id,
    )

    try:
      input_target = self.input()
      logging.info(
          "[%s] Loading data from required task target: %s",
          self.task_family,
          input_target.table_name,
      )
      generated_prompts_df = input_target.load_sentiment_data()
      self._validate_data(generated_prompts_df)

      generated_prompts_df["request"] = (
          generated_prompts_df.apply(self.construct_text_llm_prompt, axis=1)
      )
      self.output().write_sentiment_data(generated_prompts_df)

      logging.info(
          "[%s] Successfully generated and saved %d prompts.",
          self.task_family,
          len(generated_prompts_df),
      )

    except Exception as e:  # pylint: disable=broad-exception-caught
      logging.exception(
          "[%s] Task failed during execution %s due to %s: %s",
          self.task_family,
          self.execution_id,
          type(e).__name__,
          e,
      )
      raise

  def construct_text_llm_prompt(self, row: pd.Series) -> str:
    """Function for constructing a LLM prompt.

    This method generates a prompt for the LLM based on the content of the row.

    Args:
      row: A pandas series containing social content data.

    Returns:
      A pandas series containing the LLM prompt
    """
    response_schema = copy.deepcopy(constants.BASE_SENTIMENT_RESPONSE_SCHEMA)

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

    prompt_generator.build()

  def _generate_base_prompt(self, row: pd.Series) -> str:
    """Generates the base prompt for the LLM.

    Args:
      row: A row containing comment data.

    Returns:
      The base prompt for the LLM.
    """
    yt_video_summary = row["videoSummary"]
    yt_video_comment = row["text"]

    scoring_prompt = string.Template(SENTIMENT_SCORE_PROMPT_TEMPLATE)
    prompt = scoring_prompt.substitute(
        topic_list=self.workflow_exec.topic,
        video_summary=yt_video_summary,
        video_comment=yt_video_comment
    )

    return prompt
