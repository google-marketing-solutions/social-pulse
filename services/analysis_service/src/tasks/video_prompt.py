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
"""Task to generate Gemini prompts."""
import copy
import logging
import string
import pandas as pd
from pipeline.scoring import constants
from prompts import generator
from socialpulse_common import config
from tasks import core as tasks_core
from tasks.youtube_data import FindYoutubeVideos

settings = config.Settings()

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


class GenerateGeminiVideoAnalaysisPrompts(tasks_core.SentimentTask):
  """Luigi Task to generate prompts for the Gemini model.

  This task will generate prompts based on some input data (e.g., a list of
  topics, keywords, or existing text) and save them using the configured
  SentimentDataRepo.
  """

  _FINAL_OUTPUT_COLUMNS = [
      "promptId",
      "promptText",
      "generatedAt",
      "sourceDataId",  # ID of the data used to generate the prompt
  ]

  def requires(self) -> FindYoutubeVideos:
    """This task requires FindYoutubeVideos to run first.

    The actual instance is passed via the 'my_required_task' parameter
    during instantiation.

    Returns:
      The required FindYoutubeVideos task instance.
    """
    required_task = super().requires()
    if not isinstance(required_task, FindYoutubeVideos):
      raise TypeError(
          f"[{self.task_family}] requires FindYoutubeVideos, but got "
          f"{type(required_task).__name__}"
      )
    return required_task

  def output(self) -> tasks_core.SentimentDataRepoTarget:
    """Defines the output target for this task using SentimentDataRepoTarget.

    The output is a dataset managed by the SentimentDataRepo, named using
    the task family (GenerateGeminiPrompts) and execution ID.

    Returns:
      An instance of SentimentDataRepoTarget representing the task's
      output dataset.
    """
    return tasks_core.SentimentDataRepoTarget(self.dataset_name)

  def run(self, brand_or_product) -> None:
    """Executes the Gemini prompt generation logic."""
    logging.info(
        "[%s] Starting GenerateGeminiPrompts task for execution ID: %s",
        self.task_family,
        self.execution_id,
    )

    self.topic = brand_or_product

    try:
      input_target = self.input()
      logging.info(
          "[%s] Loading data from required task target: %s",
          self.task_family,
          input_target.table_name,
      )
      input_data_df = input_target.load_video_data()

      logging.info(
          "[%s] Generating Gemini prompts...", self.task_family
      )

      # Example of dummy data for generated prompts
      generated_prompts_data = self._attach_request_fn(input_data_df)
      generated_prompts_df = pd.DataFrame(generated_prompts_data)

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

    except Exception as e:
      logging.exception(
          "[%s] Task failed during execution %s due to %s: %s",
          self.task_family,
          self.execution_id,
          type(e).__name__,
          e,
      )
      raise

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

  def _generate_base_prompt(self) -> str:
    """Generates the base prompt for the LLM.

    Returns:
      The base prompt for the LLM.
    """
    scoring_prompt = string.Template(SENTIMENT_SCORE_PROMPT_TEMPLATE)
    prompt = scoring_prompt.substitute(
        topic_list=self.topic
    )

    return prompt
