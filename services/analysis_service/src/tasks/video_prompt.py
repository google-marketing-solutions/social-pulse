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
"""Task to generate LLM prompts to analyze video content."""
import copy
import logging
import string

import pandas as pd
from pipeline.scoring import constants
from prompts import generator
from tasks import core as tasks_core


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


class GenerateLlmVideoAnalysisPrompts(tasks_core.SentimentTask):
  """Luigi Task to generate prompts for the Llm model.

  This task will generate prompts based on some input data (e.g., a list of
  topics, keywords, or existing text) and save them using the configured
  SentimentDataRepo.
  """

  _INPUT_COLUMNS = [
      "videoId",
      "videoTitle",
      "videoDescription",
      "videoUrl",
      "channelId",
      "channelTitle",
      "publishedAt",
  ]

  _FINAL_OUTPUT_COLUMNS = [
      "prompt",
  ]

  def _validate_data(self, data: pd.DataFrame):
    """Function for validating the YouTube data Dataframe.

    This method validates the TouTube data dataframe by checking the
    presence of the required columns.

    Args:
      data: A dataframe containing YouTube videos data.

    Returns:
      True if the validation is successful.
    """

    for column in self._INPUT_COLUMNS:
      if column not in data.columns:
        raise ValueError(
            f"[{self.task_family}] videos dataFrame missing "
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
      if self._validate_data(generated_prompts_df):
        logging.info(
            "[%s] Generating video Llm prompts...", self.task_family
        )

        generated_prompts_df["prompt"] = (
            generated_prompts_df.apply(self._construct_video_llm_prompt, axis=1)
        )

        # Ensure all final output columns are present
        for col in self._FINAL_OUTPUT_COLUMNS:
          if col not in generated_prompts_df.columns:
            generated_prompts_df[col] = pd.NA

        self.output().write_sentiment_data(
            generated_prompts_df[self._FINAL_OUTPUT_COLUMNS]
        )
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

  def _construct_video_llm_prompt(self, row: pd.Series) -> pd.Series:
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
            self._generate_base_prompt()
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

    return pd.Series({
        "prompt": prompt_generator.build()
    })

  def _generate_base_prompt(self) -> str:
    """Generates the base prompt for the LLM.

    Returns:
      The base prompt for the LLM.
    """
    scoring_prompt = string.Template(SENTIMENT_SCORE_PROMPT_TEMPLATE)
    prompt = scoring_prompt.substitute(
        topic_list=self.workflow_exec.topic
    )

    return prompt
