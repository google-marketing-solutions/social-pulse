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

"""Unit tests for markdown utility."""

import unittest
from socialpulse_common.utils import markdown


class MarkdownUtilsTest(unittest.TestCase):
  """Tests for markdown utility functions."""

  def test_strip_markdown_code_blocks_with_json_language_tag(self):
    """Tests stripping markdown with a json language tag."""
    text = "```json\n{\"key\": \"value\"}\n```"
    expected = "{\"key\": \"value\"}"
    self.assertEqual(markdown.strip_markdown_code_blocks(text), expected)

  def test_strip_markdown_code_blocks_with_no_language_tag(self):
    """Tests stripping markdown with no language tag."""
    text = "```\n{\"key\": \"value\"}\n```"
    expected = "{\"key\": \"value\"}"
    self.assertEqual(markdown.strip_markdown_code_blocks(text), expected)

  def test_strip_markdown_code_blocks_one_line(self):
    """Tests stripping markdown on a single line."""
    text = "```json{\"key\": \"value\"}```"
    expected = "{\"key\": \"value\"}"
    self.assertEqual(markdown.strip_markdown_code_blocks(text), expected)

  def test_strip_markdown_code_blocks_no_json_tag_one_line(self):
    """Tests stripping markdown on a single line with no tag."""
    text = "```{\"key\": \"value\"}```"
    expected = "{\"key\": \"value\"}"
    self.assertEqual(markdown.strip_markdown_code_blocks(text), expected)

  def test_strip_markdown_code_blocks_with_surrounding_whitespace(self):
    """Tests stripping markdown with surrounding whitespace."""
    text = "  \n```json\n{\"key\": \"value\"}\n```  \n"
    expected = "{\"key\": \"value\"}"
    self.assertEqual(markdown.strip_markdown_code_blocks(text), expected)

  def test_strip_markdown_code_blocks_with_no_markdown(self):
    """Tests stripping markdown with no markdown formatting."""
    text = "{\"key\": \"value\"}"
    self.assertEqual(markdown.strip_markdown_code_blocks(text), text)


if __name__ == "__main__":
  unittest.main()
