import unittest


import pandas as pd
import parameterized
import sentiment_task_mixins as test_mixins
from tasks import text_prompt


class TestGenerateLlmTextAnalysisPrompts(
    unittest.TestCase,
    test_mixins.SetupMockSentimentTaskDepependenciesMixin
):
  def setUp(self):
    """Set up for test methods."""
    super().setUp()

    self.setup_all_mock_dependencies()
    self._setup_mock_prompt_generator()

    self.mock_execution_params.topic = "some_topic"

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
    self.patcher_generator = (unittest.mock
                              .patch("prompts.generator.LlmPromptGenerator",
                                     return_value=self.mock_prompt_generator))
    self.mock_llm_prompt_generator_class = self.patcher_generator.start()

  def tearDown(self):
    """Clean up after test methods."""
    super().tearDown()
    self.patcher_generator.stop()

  @parameterized.parameterized.expand([
      (
          "Comment ID",
          pd.DataFrame({
              "videoId": ["video1"],
              "authorId": ["author1"],
              "videoSummary": ["here's a summary"],
              "text": ["here's a comment"],
              "parentId": ["parent1"]
          }),
          "commentId"
      ),
      (
          "Video ID",
          pd.DataFrame({
              "commentId": ["comment1"],
              "authorId": ["author1"],
              "videoSummary": ["here's a summary"],
              "text": ["here's a comment"],
              "parentId": ["parent1"]
          }),
          "videoId"
      ),
      (
          "Author ID",
          pd.DataFrame({
              "commentId": ["comment1"],
              "videoId": ["video1"],
              "videoSummary": ["here's a summary"],
              "text": ["here's a comment"],
              "parentId": ["parent1"]
          }),
          "authorId"
      ),
      (
          "Video Summary",
          pd.DataFrame({
              "commentId": ["comment1"],
              "videoId": ["video1"],
              "authorId": ["author1"],
              "text": ["here's a comment"],
              "parentId": ["parent1"]
          }),
          "videoSummary"
      ),
      (
          "Comment Text",
          pd.DataFrame({
              "commentId": ["comment1"],
              "videoId": ["video1"],
              "authorId": ["author1"],
              "videoSummary": ["here's a summary"],
              "parentId": ["parent1"]
          }),
          "text"
      ),
      (
          "Parent ID",
          pd.DataFrame({
              "commentId": ["comment1"],
              "videoId": ["video1"],
              "authorId": ["author1"],
              "videoSummary": ["here's a summary"],
              "text": ["here's a comment"],
          }),
          "parentId"
      )
  ])
  def test_fails_if_required_column_is_missing(
      self,
      _,
      input_pd,
      missing_col_name
  ):
    """Test that the task fails if a required column is missing.

    Given the input data is missing a required column
    When the task is executed
    Then a ValueError is raised
    And the error specifies the missing column

    Args:
        _: Placeholder for the parameterized test name.
        input_pd: A pandas DataFrame representing the input data to the task,
          with one required column missing.
        missing_col_name: The name of the missing column that should be present
          in the raised error message.
    """
    self.mock_input_target.load_sentiment_data.return_value = input_pd
    with self.assertRaises(ValueError) as cm:
      task = text_prompt.GenerateLlmTextAnalysisPrompts(
          execution_id="some_execution_id",
          my_required_task=self.mock_required_task
      )
      task.run()

    self.assertIn(missing_col_name, str(cm.exception))

  def test_a_prompt_column_is_added_to_output_dataframe(self):
    """Tests that a column is added to the output with a prompt.

    Given a properly populated input sentiment dataset
    When the task is executed
    Then a prompt column is present in the output sentiment dataset
    """
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "commentId": ["comment1"],
        "videoId": ["video1"],
        "authorId": ["author1"],
        "videoSummary": ["here's a summary"],
        "text": ["here's a comment"],
        "parentId": ["parent1"]
    })

    task = text_prompt.GenerateLlmTextAnalysisPrompts(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    write_sentiment_args = (
        self.mock_sentiment_data_repo.write_sentiment_data.call_args
    )
    output_df = write_sentiment_args.args[1]
    self.assertIn("prompt", output_df.columns)

  def test_prompt_is_generated_with_topic(self):
    self.mock_execution_params.topic = "some_important_topic"
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "commentId": ["comment1"],
        "videoId": ["video1"],
        "authorId": ["author1"],
        "videoSummary": ["here's a summary"],
        "text": ["here's a comment"],
        "parentId": ["parent1"]
    })

    task = text_prompt.GenerateLlmTextAnalysisPrompts(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    with_prompt_args = self.mock_prompt_generator.with_prompt.call_args
    actual_prompt = with_prompt_args.args[0]
    self.assertIn("some_important_topic", actual_prompt)

  def test_prompt_is_generated_with_video_summary(self):
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "commentId": ["comment1"],
        "videoId": ["video1"],
        "authorId": ["author1"],
        "videoSummary": ["here's a summary"],
        "text": ["here's a comment"],
        "parentId": ["parent1"]
    })

    task = text_prompt.GenerateLlmTextAnalysisPrompts(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    with_prompt_args = self.mock_prompt_generator.with_prompt.call_args
    actual_prompt = with_prompt_args.args[0]
    self.assertIn("here's a summary", actual_prompt)

  def test_prompt_is_generated_with_comment_text(self):
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "commentId": ["comment1"],
        "videoId": ["video1"],
        "authorId": ["author1"],
        "videoSummary": ["here's a summary"],
        "text": ["here's a comment"],
        "parentId": ["parent1"]
    })

    task = text_prompt.GenerateLlmTextAnalysisPrompts(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    with_prompt_args = self.mock_prompt_generator.with_prompt.call_args
    actual_prompt = with_prompt_args.args[0]
    self.assertIn("here's a comment", actual_prompt)


if __name__ == "__main__":
  unittest.main()
