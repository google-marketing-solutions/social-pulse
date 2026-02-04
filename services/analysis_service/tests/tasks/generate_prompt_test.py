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

import unittest

import pandas as pd
from prompts import promptconfig
from prompts.configs import core as prompt_core
import sentiment_task_mixins as test_mixins
from tasks import generate_prompt


class TestGenerateLlmVideoAnalysisPrompts(
    unittest.TestCase,
    test_mixins.SetupMockSentimentTaskDepependenciesMixin
):

  def setUp(self):
    """Set up for test methods."""
    super().setUp()

    self.setup_all_mock_dependencies()
    self.mock_execution_params.topic = "some_topic"

    self._setup_mock_prompt_generator()
    self._setup_mock_prompt_config()
    self._setup_mock_prompt_config_factory()

  def _setup_mock_prompt_generator(self):
    self.mock_prompt_generator = unittest.mock.MagicMock()
    (self.mock_prompt_generator.with_prompt
     .return_value) = self.mock_prompt_generator
    (self.mock_prompt_generator.with_system_instruction
     .return_value) = self.mock_prompt_generator
    (self.mock_prompt_generator.with_response_schema
     .return_value) = self.mock_prompt_generator
    (self.mock_prompt_generator.with_temperature
     .return_value) = self.mock_prompt_generator
    (self.mock_prompt_generator.with_response_mime_type
     .return_value) = self.mock_prompt_generator
    (self.mock_prompt_generator.with_file_data
     .return_value) = self.mock_prompt_generator
    self.mock_prompt_generator.build.return_value = "generated_llm_prompt"

    # Patch the LlmPromptGenerator in the module
    self.patcher_generator = (
        unittest.mock.patch(
            "tasks.generate_prompt.generator.LlmPromptGenerator",
            return_value=self.mock_prompt_generator
        )
    )
    self.mock_llm_prompt_generator_class = self.patcher_generator.start()

  def _setup_mock_prompt_config(self):
    self.mock_prompt_config = unittest.mock.Mock(
        spec=prompt_core.PromptConfig
    )
    self.mock_prompt_config.get_input_columns.return_value = [
        "column1",
        "column2",
    ]
    self.mock_prompt_config.get_system_instruction.return_value = (
        "system_instruction"
    )
    self.mock_prompt_config.generate_llm_prompt.return_value = (
        "generated_llm_prompt"
    )
    self.mock_prompt_config.get_response_schema.return_value = (
        "response_schema"
    )
    self.mock_prompt_config.get_file_data.return_value = None

  def _setup_mock_prompt_config_factory(self):
    self.mock_prompt_config_factory = unittest.mock.Mock(
        spec=promptconfig.PromptConfigFactory
    )
    self.mock_prompt_config_factory.get_prompt_config.return_value = (
        self.mock_prompt_config
    )

    self._prompt_config_factory_patcher = unittest.mock.patch(
        "tasks.generate_prompt.promptconfig.PromptConfigFactory",
        return_value=self.mock_prompt_config_factory
    )
    self.mock_prompt_config_factory_class = (
        self._prompt_config_factory_patcher.start()
    )

  def tearDown(self):
    """Clean up after test methods."""
    super().tearDown()
    self.patcher_generator.stop()
    self._prompt_config_factory_patcher.stop()

  def test_fails_if_required_input_column_is_missing(self):
    """Test that the task fails if a required column is missing.

    Given the input data is missing a required column
    When the task is executed
    Then a ValueError is raised
    And the error specifies the missing columns
    """
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "column1": [1, 2, 3],
    })
    with self.assertRaises(ValueError) as cm:
      task = generate_prompt.GenerateLlmPromptForContentTask(
          execution_id="some_execution_id",
          my_required_task=self.mock_required_task
      )
      task.run()

    self.assertIn("column2", str(cm.exception))

  def test_uses_prompt_config_factory_to_get_prompt_config(self):
    """Test that the prompt config factory is used to get the prompt config.

    Given a properly populated input sentiment dataset
    When the task is executed
    Then the prompt config factory is used to get the prompt config
    """
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "column1": [1, 2, 3],
        "column2": [4, 5, 6]
    })

    task = generate_prompt.GenerateLlmPromptForContentTask(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    self.mock_prompt_config_factory_class.assert_called_once_with(
        self.mock_execution_params
    )
    mock_factory = self.mock_prompt_config_factory_class.return_value
    mock_factory.get_prompt_config.assert_called_once()

  def test_uses_prompt_config_to_generate_prompt(self):
    """Test that the prompt config is used to generate the prompt.

    Given a properly populated input sentiment dataset
    When the task is executed
    Then the prompt config is used to generate the prompt
    """
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "column1": [1],
        "column2": [4]
    })

    task = generate_prompt.GenerateLlmPromptForContentTask(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    self.mock_prompt_generator.with_prompt.assert_called_once_with(
        "generated_llm_prompt"
    )
    self.mock_prompt_generator.with_system_instruction.assert_called_once_with(
        "system_instruction"
    )
    self.mock_prompt_generator.with_response_schema.assert_called_once_with(
        "response_schema"
    )

  def test_includes_file_data_if_config_provides_it(self):
    """Tests that file data is included in the prompt if provided by the config.
    """
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "column1": [1],
        "column2": [4]
    })
    self.mock_prompt_config.get_file_data.return_value = "file_data"

    task = generate_prompt.GenerateLlmPromptForContentTask(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    self.mock_prompt_generator.with_file_data.assert_called_once_with(
        "file_data"
    )

  def test_a_request_column_is_added_to_output_dataframe(self):
    """Tests that a request column is added to the output dataframe.

    Given a properly populated input sentiment dataset
    When the task is executed
    Then a request column is present in the output sentiment dataset
    """
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "column1": [1],
        "column2": [4]
    })

    task = generate_prompt.GenerateLlmPromptForContentTask(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    write_sentiment_args = (
        self.mock_sentiment_data_repo.write_sentiment_data.call_args
    )
    output_df = write_sentiment_args.args[1]
    self.assertIn("request", output_df.columns)

    request_prompt = output_df["request"][0]
    self.assertIn("generated_llm_prompt", request_prompt)
