
import unittest

import pandas as pd
import parameterized
import sentiment_task_mixins as test_mixins
from tasks import video_prompt


class TestGenerateLlmVideoAnalysisPrompts(
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
          "Video ID",
          pd.DataFrame({
              "videoTitle": ["title1"],
              "videoDescription": ["desc1"],
              "videoUrl": ["https://video_url"],
              "channelId": ["channel1"],
              "channelTitle": ["channelTitle1"],
              "publishedAt": ["date1"]
          }),
          "videoId"
      ),
      (
          "Video Title",
          pd.DataFrame({
              "videoId": ["id1"],
              "videoDescription": ["desc1"],
              "videoUrl": ["https://video_url"],
              "channelId": ["channel1"],
              "channelTitle": ["channelTitle1"],
              "publishedAt": ["date1"]
          }),
          "videoTitle"
      ),
      (
          "Video Description",
          pd.DataFrame({
              "videoId": ["id1"],
              "videoTitle": ["title1"],
              "videoUrl": ["https://video_url"],
              "channelId": ["channel1"],
              "channelTitle": ["channelTitle1"],
              "publishedAt": ["date1"]
          }),
          "videoDescription"
      ),
      (
          "Video URL",
          pd.DataFrame({
              "videoId": ["id1"],
              "videoTitle": ["title1"],
              "videoDescription": ["desc1"],
              "channelId": ["channel1"],
              "channelTitle": ["channelTitle1"],
              "publishedAt": ["date1"]
          }),
          "videoUrl"
      ),
      (
          "Channel ID",
          pd.DataFrame({
              "videoId": ["id1"],
              "videoTitle": ["title1"],
              "videoDescription": ["desc1"],
              "videoUrl": ["https://video_url"],
              "channelTitle": ["channelTitle1"],
              "publishedAt": ["date1"]
          }),
          "channelId"
      ),
      (
          "Channel Title",
          pd.DataFrame({
              "videoId": ["id1"],
              "videoTitle": ["title1"],
              "videoDescription": ["desc1"],
              "videoUrl": ["https://video_url"],
              "channelId": ["channel1"],
              "publishedAt": ["date1"]
          }),
          "channelTitle"
      ),
      (
          "Published At",
          pd.DataFrame({
              "videoId": ["id1"],
              "videoTitle": ["title1"],
              "videoDescription": ["desc1"],
              "videoUrl": ["https://video_url"],
              "channelId": ["channel1"],
              "channelTitle": ["channelTitle1"]
          }),
          "publishedAt"
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
    And the error specifies the missing columns

    Args:
      _: Placeholder for the parameterized test name.
      input_pd: A pandas DataFrame representing the input data to the task,
          with one required column missing.
      missing_col_name: The name of the missing column that should be present in
          the raised error message.
    """
    self.mock_input_target.load_sentiment_data.return_value = input_pd
    with self.assertRaises(ValueError) as cm:
      task = video_prompt.GenerateLlmVideoAnalysisPrompts(
          execution_id="some_execution_id",
          my_required_task=self.mock_required_task
      )
      task.run()

    self.assertIn(missing_col_name, str(cm.exception))

  def test_a_request_column_is_added_to_output_dataframe(self):
    """Tests that a request column is added to the output dataframe.

    Given a properly populated input sentiment dataset
    When the task is executed
    Then a request column is present in the output sentiment dataset
    """
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "videoId": ["id1"],
        "videoTitle": ["title1"],
        "videoDescription": ["desc1"],
        "channelId": ["channel1"],
        "channelTitle": ["channelTitle1"],
        "publishedAt": ["date1"],
        "videoUrl": ["url1"]
    })

    task = video_prompt.GenerateLlmVideoAnalysisPrompts(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    write_sentiment_args = (
        self.mock_sentiment_data_repo.write_sentiment_data.call_args
    )
    output_df = write_sentiment_args.args[1]
    self.assertIn("request", output_df.columns)

  def test_prompt_column_has_topic_added_to_llm_prompt(self):
    """Tests that a column is added to the output with a prompt.

    Given the workflow exec has the topic "included_topic"
    When the task is executed
    Then the prompt includes the topic
    """
    self.mock_execution_params.topic = "included_topic"
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "videoId": ["id1"],
        "videoTitle": ["title1"],
        "videoDescription": ["desc1"],
        "channelId": ["channel1"],
        "channelTitle": ["channelTitle1"],
        "publishedAt": ["date1"],
        "videoUrl": ["url1"]
    })

    task = video_prompt.GenerateLlmVideoAnalysisPrompts(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    with_prompt_args = self.mock_prompt_generator.with_prompt.call_args
    provided_prompt = with_prompt_args[0][0]
    self.assertIn("included_topic", provided_prompt)

  def test_prompt_is_generated_with_video_url(self):
    """Tests that the video url is added to the prompt."""
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame({
        "videoId": ["id1"],
        "videoTitle": ["title1"],
        "videoDescription": ["desc1"],
        "channelId": ["channel1"],
        "channelTitle": ["channelTitle1"],
        "publishedAt": ["date1"],
        "videoUrl": ["http://video.url"]
    })

    task = video_prompt.GenerateLlmVideoAnalysisPrompts(
        execution_id="some_execution_id",
        my_required_task=self.mock_required_task
    )
    task.run()

    self.mock_prompt_generator.with_file_data.assert_called_with([
        ("video/*", "http://video.url")
    ])


if __name__ == "__main__":
  unittest.main()
