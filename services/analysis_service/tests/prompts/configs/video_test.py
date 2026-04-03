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
"""Unit tests for video prompt configurations."""

import unittest
from unittest import mock

import pandas as pd
from prompts.configs import video


class TestBasicSentimentScoreFromVideoPromptConfig(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.mock_workflow_exec = mock.Mock()
    self.mock_workflow_exec.topic = "test_brand"
    self.mock_workflow_exec.include_justifications = False
    self.config = video.BasicSentimentScoreFromVideoPromptConfig(
        self.mock_workflow_exec
    )

  def test_get_input_columns(self):
    """Tests get_input_columns returns correct columns.

    Given a BasicSentimentScoreFromVideoPromptConfig
    When get_input_columns is called
    Then it returns the list of video input columns
    """
    columns = self.config.get_input_columns()
    self.assertIn("videoId", columns)
    self.assertIn("videoUrl", columns)

  def test_get_system_instruction(self):
    """Tests get_system_instruction returns correct instruction.

    Given a BasicSentimentScoreFromVideoPromptConfig
    When get_system_instruction is called
    Then it returns the video extraction system instruction
    """
    instruction = self.config.get_system_instruction()
    self.assertIn("Act as an expert research analyst", instruction)

  def test_get_file_data(self):
    """Tests get_file_data returns correct file data.

    Given a BasicSentimentScoreFromVideoPromptConfig and a row with videoUrl
    When get_file_data is called
    Then it returns a list with the video MIME type and URL
    """
    row = pd.Series({"videoUrl": "http://example.com/video.mp4"})
    file_data = self.config.get_file_data(row)
    self.assertEqual(file_data, [("video/*", "http://example.com/video.mp4")])

  def test_generate_llm_prompt_without_justifications(self):
    """Tests generate_llm_prompt without justifications.

    Given a BasicSentimentScoreFromVideoPromptConfig with
      include_justifications=False
    When generate_llm_prompt is called
    Then it returns the prompt without the justification stanza
    """
    row = pd.Series({"videoUrl": "http://example.com/video.mp4"})
    prompt = self.config.generate_llm_prompt(row)
    self.assertIn("test_brand", prompt)
    self.assertNotIn("verbatim quotes", prompt)

  def test_generate_llm_prompt_with_justifications(self):
    """Tests generate_llm_prompt with justifications.

    Given a BasicSentimentScoreFromVideoPromptConfig with
      include_justifications=True
    When generate_llm_prompt is called
    Then it returns the prompt with the justification stanza
    """
    self.mock_workflow_exec.include_justifications = True
    row = pd.Series({"videoUrl": "http://example.com/video.mp4"})
    prompt = self.config.generate_llm_prompt(row)
    self.assertIn("test_brand", prompt)
    self.assertIn("verbatim quotes", prompt)

  def test_get_response_schema_without_justifications(self):
    """Tests get_response_schema without justifications.

    Given a BasicSentimentScoreFromVideoPromptConfig with
      include_justifications=False
    When get_response_schema is called
    Then it returns the schema without justifications property
    """
    schema = self.config.get_response_schema()
    sentiment_properties = schema["properties"]["sentiments"]["items"][
        "properties"
    ]
    self.assertNotIn("justifications", sentiment_properties)

  def test_get_response_schema_with_justifications(self):
    """Tests get_response_schema with justifications.

    Given a BasicSentimentScoreFromVideoPromptConfig with
      include_justifications=True
    When get_response_schema is called
    Then it returns the schema with justifications property
    """
    self.mock_workflow_exec.include_justifications = True
    schema = self.config.get_response_schema()
    sentiment_properties = schema["properties"]["sentiments"]["items"][
        "properties"
    ]
    self.assertIn("justifications", sentiment_properties)


class TestShareOfVoiceSentimentScoresFromVideoPromptConfig(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.mock_workflow_exec = mock.Mock()
    self.mock_workflow_exec.topic = "test_topic"
    self.mock_workflow_exec.include_justifications = False
    self.config = video.ShareOfVoiceSentimentScoresFromVideoPromptConfig(
        self.mock_workflow_exec
    )

  def test_generate_llm_prompt(self):
    """Tests generate_llm_prompt for SoV.

    Given a ShareOfVoiceSentimentScoresFromVideoPromptConfig
    When generate_llm_prompt is called
    Then it returns the SoV prompt
    """
    row = pd.Series({"videoUrl": "http://example.com/video.mp4"})
    prompt = self.config.generate_llm_prompt(row)
    self.assertIn("test_topic", prompt)

  def test_get_response_schema(self):
    """Tests get_response_schema for SoV.

    Given a ShareOfVoiceSentimentScoresFromVideoPromptConfig
    When get_response_schema is called
    Then it returns the schema with weight property
    """
    schema = self.config.get_response_schema()
    sentiment_properties = schema["properties"]["sentiments"]["items"][
        "properties"
    ]
    self.assertIn("weight", sentiment_properties)
