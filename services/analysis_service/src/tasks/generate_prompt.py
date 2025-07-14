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
"""Task to generate LLM prompts based on the workflow execution params."""

import logging

import pandas as pd
from prompts import generator
from prompts import promptconfig
from tasks import core as tasks_core


logger = logging.getLogger(__name__)


class GenerateLlmPromptForContentTask(tasks_core.SentimentTask):
  """Base Luigi Task to generate prompts for the LLM model.

  This task handles the common logic for generating LLM prompts,
  delegating specific prompt generation details to a PromptConfig instance.
  """

  _FINAL_OUTPUT_COLUMNS = [
      "prompt",
  ]

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._prompt_config: promptconfig.PromptConfig = (
        promptconfig.PromptConfigFactory(self.workflow_exec).get_prompt_config()
    )

  def _validate_data(self, data: pd.DataFrame):
    """Function for validating the input DataFrame.

    This method validates the input dataframe by checking the
    presence of the required columns, as determined by the prompt config.

    Args:
      data: A dataframe containing input data.

    Returns:
      True if the validation is successful.
    """
    for column in self._prompt_config.get_input_columns():
      if column not in data.columns:
        raise ValueError(
            f"[{self.task_family}] input dataFrame missing "
            f"'{column}' column."
        )
    return True

  def run(self) -> None:
    """Executes the LLM prompt generation logic."""
    logging.info(
        "[%s] Starting prompt generation task for execution ID: %s",
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
          generated_prompts_df.apply(self._construct_llm_prompt, axis=1)
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

  def _construct_llm_prompt(self, row: pd.Series) -> str:
    """Function for constructing a LLM prompt using the configured strategy.

    This method generates a prompt for the LLM based on the content of the row
    and the specific PromptConfig.

    Args:
      row: A pandas series containing social content data.

    Returns:
      A pandas series containing the LLM prompt
    """
    prompt_generator: generator.LlmPromptGenerator = (
        generator.LlmPromptGenerator()
        .with_prompt(
            self._prompt_config.generate_llm_prompt(row)
        )
        .with_system_instruction(
            self._prompt_config.get_system_instruction()
        )
        .with_response_schema(
            self._prompt_config.get_response_schema()
        )
        .with_temperature(
            0.5
        )
        .with_response_mime_type(
            "application/json"
        )
    )

    file_data = self._prompt_config.get_file_data(row)
    if file_data:
      prompt_generator.with_file_data(file_data)

    return prompt_generator.build()
