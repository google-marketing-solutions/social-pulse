import string
import unittest
import pandas as pd
from video_prompt import GenerateLlmVideoAnalysisPrompts
from video_prompt import SENTIMENT_SCORE_PROMPT_TEMPLATE
from video_prompt import VIDEO_EXTRACTION_SYSTEM_INSTRUCTION


class TestGenerateLlmVideoAnalysisPrompts(unittest.TestCase):

  def setUp(self):
    """Set up for test methods."""
    super().setUp()
    # Mock external dependencies
    self.mock_settings = unittest.mock.MagicMock()
    with unittest.mock.patch("socialpulse_common.config.Settings",
                             return_value=self.mock_settings):
      self.task = GenerateLlmVideoAnalysisPrompts(
          dataset_name="test_dataset", execution_id="test_exec_id")
      self.task.topic = "TestProduct"  # Set a default topic for testing

    # Mock constants
    self.mock_base_sentiment_response_schema = {
        "items": {"properties": {"sentiment": {}, "relevance": {}}}
    }
    self.mock_justification_response_schema = {
        "positive_quotes": {}, "negative_quotes": {}
    }
    with (unittest.mock
          .patch("pipeline.scoring.constants.BASE_SENTIMENT_RESPONSE_SCHEMA",
                 self.mock_base_sentiment_response_schema)), \
         (unittest.mock
          .patch("pipeline.scoring.constants.JUSTIFICATION_RESPONSE_SCHEMA",
                 self.mock_justification_response_schema)):
      # Re-instantiate the task to ensure mocked constants are picked up
      self.task = GenerateLlmVideoAnalysisPrompts(
          dataset_name="test_dataset", execution_id="test_exec_id")
      self.task.topic = "TestProduct"

    # Mock LlmPromptGenerator
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
    self.patcher_generator = (unittest.mock
                              .patch("prompts.generator.LlmPromptGenerator",
                                     return_value=self.mock_prompt_generator))
    self.mock_llm_prompt_generator_class = self.patcher_generator.start()

    # Patch logging to prevent actual log output during tests
    self.patcher_logging = unittest.mock.patch("logging.info")
    self.mock_logging_info = self.patcher_logging.start()
    self.patcher_logging_exception = unittest.mock.patch("logging.exception")
    self.mock_logging_exception = self.patcher_logging_exception.start()

  def tearDown(self):
    """Clean up after test methods."""
    self.patcher_generator.stop()
    self.patcher_logging.stop()
    self.patcher_logging_exception.stop()
    super().tearDown()

  def test_validate_data(self):
    """Test validate_data method."""
    data = pd.DataFrame({"col1": [1], "col2": [2]})
    self.assertTrue(self.task.validate_data(data))

  @unittest.mock.patch("tasks.core.SentimentDataRepoTarget")
  def test_run_success(self, mock_sentiment_data_repo_target):
    """Test run method for successful execution."""
    mock_input_target = unittest.mock.MagicMock()
    mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "videoUrl": ["http://example.com/video1"],
        "sourceDataId": ["id1"]
    })

    self.task.input = unittest.mock.MagicMock(return_value=mock_input_target)
    mock_output_target_instance = mock_sentiment_data_repo_target.return_value
    mock_output_target_instance.write_sentiment_data.return_value = None

    self.task.run(brand_or_product="TestBrand")

    mock_input_target.load_sentiment_data.assert_called_once()
    mock_output_target_instance.write_sentiment_data.assert_called_once()
    args = mock_output_target_instance.write_sentiment_data.call_args
    output_df = args[0]
    self.assertIsInstance(output_df, pd.DataFrame)
    self.assertIn("promptId", output_df.columns)
    self.assertIn("promptText", output_df.columns)
    self.assertIn("generatedAt", output_df.columns)
    self.assertIn("sourceDataId", output_df.columns)
    self.assertEqual(len(output_df), 1)
    self.assertEqual(output_df["promptText"].iloc[0], "generated_llm_prompt")
    self.assertEqual(output_df["sourceDataId"].iloc[0], "id1")
    self.mock_logging_info.assert_called()
    self.mock_logging_exception.assert_not_called()

  @unittest.mock.patch("tasks.core.SentimentDataRepoTarget")
  def test_run_failure_loading_data(self, mock_sentiment_data_repo_target):
    """Test run method for failure when loading data."""
    mock_input_target = unittest.mock.MagicMock()
    mock_input_target.load_sentiment_data.side_effect = Exception("Test error")
    self.task.input = unittest.mock.MagicMock(return_value=mock_input_target)

    with self.assertRaises(Exception):
      self.task.run(brand_or_product="TestBrand")

    self.mock_logging_exception.assert_called_once()
    mock_input_target.load_sentiment_data.assert_called_once()
    (mock_sentiment_data_repo_target.return_value
     .write_sentiment_data.assert_not_called())

  def test_attach_request(self):
    """Test _attach_request method."""
    data = pd.DataFrame({
        "videoUrl": ["http://test.com/video_A", "http://test.com/video_B"],
        "sourceDataId": ["id_A", "id_B"]
    })

    self.task.topic = "TestProduct"

    result_df = self.task._attach_request(data)

    self.assertIsInstance(result_df, pd.DataFrame)
    self.assertEqual(len(result_df), 2)
    self.assertIn("prompt", result_df.columns)
    self.assertEqual(result_df["prompt"].iloc[0], "generated_llm_prompt")
    self.assertEqual(result_df["prompt"].iloc[1], "generated_llm_prompt")

    # Verify LlmPromptGenerator was called correctly for each row
    self.assertEqual(self.mock_llm_prompt_generator_class.call_count, 2)

    # Verify calls for the first row
    self.mock_prompt_generator.with_prompt.assert_any_call(
        self._generate_expected_base_prompt("TestProduct"))
    self.mock_prompt_generator.with_system_instruction.assert_any_call(
        VIDEO_EXTRACTION_SYSTEM_INSTRUCTION)
    self.mock_prompt_generator.with_temperature.assert_any_call(0.5)
    self.mock_prompt_generator.with_response_mime_type.assert_any_call(
        "application/json"
    )
    self.mock_prompt_generator.with_file_data.assert_any_call([
        ("video/*", "http://test.com/video_A")
    ])
    self.mock_prompt_generator.build.assert_called()

    # Verify calls for the second row (example, just checking file_data changes)
    self.mock_prompt_generator.with_file_data.assert_any_call([
        ("video/*", "http://test.com/video_B")
    ])

  def test_generate_base_prompt(self):
    """Test _generate_base_prompt method."""
    self.task.topic = "Laptop, Smartphone"
    expected_prompt = string.Template(
        SENTIMENT_SCORE_PROMPT_TEMPLATE
    ).substitute(
        topic_list="Laptop, Smartphone"
    )
    self.assertEqual(self.task._generate_base_prompt(), expected_prompt)

  def _generate_expected_base_prompt(self, topic):
    """Helper to generate the expected base prompt."""
    scoring_prompt = string.Template(SENTIMENT_SCORE_PROMPT_TEMPLATE)
    return scoring_prompt.substitute(topic_list=topic)

  def _get_expected_response_schema(self):
    """Helper to get the expected merged response schema."""
    response_schema = self.mock_base_sentiment_response_schema
    response_schema["items"]["properties"].update(
        self.mock_justification_response_schema)
    return response_schema


if __name__ == "__main__":
  unittest.main()
