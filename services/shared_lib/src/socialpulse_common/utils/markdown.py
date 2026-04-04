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

"""Markdown utility functions."""


def strip_markdown_code_blocks(text: str) -> str:
  """Strips markdown code blocks (e.g., ```json ... ```) from a string.

  Args:
    text: The string to strip markdown from.

  Returns:
    The stripped string.
  """
  text = text.strip()
  if text.startswith("```"):
    # Find the end of the first line (the language tag)
    first_newline = text.find("\n")
    if first_newline != -1:
      text = text[first_newline + 1:]
    else:
      # If no newline, just strip the opening backticks
      # (e.g. ```something```)
      if text.startswith("```json"):
        text = text[7:]
      else:
        text = text[3:]

  if text.endswith("```"):
    text = text[:-3]

  return text.strip()
