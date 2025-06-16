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
"""Library of various LLM prompt generators."""


import json


class LlmPromptGenerator:
  """A builder class for constructing prompts for Large Language Models (LLMs).

  It allows setting various parameters and configurations for the prompt.
  """
  _prompt: str
  _system_instruction: str = ""
  _file_data: tuple[str, str] = ()
  _inline_text: str = ""
  _response_schema: dict[str, any] = {}
  _temperature: float = 0.0
  _max_output_tokens: int = 8192
  _response_mime_type: str = "application/json"

  def with_prompt(self, prompt: str) -> "LlmPromptGenerator":
    """Sets the base prompt for the LLM.

    Args:
      prompt: The base text prompt for the LLM.

    Returns:
      The LlmPromptGenerator instance for method chaining.
    """
    self._prompt = prompt
    return self

  def with_system_instruction(
      self, system_instruction: str) -> "LlmPromptGenerator":
    """Sets the system instruction for the LLM.

    Args:
      system_instruction: The system instruction text.

    Returns:
      The LlmPromptGenerator instance for method chaining.
    """
    self._system_instruction = system_instruction
    return self

  def with_file_data(
      self, file_data: list[tuple[str, str]]) -> "LlmPromptGenerator":
    """Sets the file data to be included in the prompt.

    Args:
      file_data: A tuple containing the mime type and file URI.

    Returns:
      The LlmPromptGenerator instance for method chaining.
    """
    self._file_data = file_data
    return self

  def with_response_schema(
      self, response_schema: dict[str, any]) -> "LlmPromptGenerator":
    """Sets the expected response schema for the LLM.

    Args:
      response_schema: A dictionary representing the JSON schema of the expected
      response.

    Returns:
      The LlmPromptGenerator instance for method chaining.
    """
    self._response_schema = response_schema
    return self

  def with_temperature(
      self, temperature: float) -> "LlmPromptGenerator":
    """Sets the temperature for the LLM's response generation.

    Args:
      temperature: The temperature value (0.0 for deterministic, higher for more
      creative).

    Returns:
      The LlmPromptGenerator instance for method chaining.
    """
    self._temperature = temperature
    return self

  def with_max_output_tokens(
      self, max_output_tokens: int) -> "LlmPromptGenerator":
    """Sets the maximum number of output tokens for the LLM's response.

    Args:
      max_output_tokens: The maximum number of tokens in the response.

    Returns:
      The LlmPromptGenerator instance for method chaining.
    """
    self._max_output_tokens = max_output_tokens
    return self

  def with_response_mime_type(
      self, response_mime_type: str) -> "LlmPromptGenerator":
    """Sets the expected MIME type of the LLM's response.

    Args:
      response_mime_type: The MIME type of the response (e.g.,
      "application/json").

    Returns:
      The LlmPromptGenerator instance for method chaining.
    """
    self._response_mime_type = response_mime_type
    return self

  def with_inline_text(self, inline_text: str) -> "LlmPromptGenerator":
    """Sets the inline text to be included in the prompt.

    Args:
      inline_text: The inline text to be included.

    Returns:
      The LlmPromptGenerator instance for method chaining.
    """
    self._inline_text = inline_text
    return self

  def build(self) -> str:
    """Builds the prompt structure and returns it as a JSON string."""
    # For details on the batch prompt structure used for the generated prompt:
    # https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference#parts
    prompt_structure = {
        "systemInstruction": {
            "parts": [
                {"text": self._system_instruction}
            ]
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": self._prompt
                    },
                ],
            }
        ],
        "generationConfig": {
            "temperature": self._temperature,
            "maxOutputTokens": self._max_output_tokens,
            "responseMimeType": self._response_mime_type,
            "responseSchema": self._response_schema,
        },
    }

    if self._file_data:
      for file_data in self._file_data:
        file_part_definition = {
            "fileData": {
                "mimeType": file_data[0],
                "fileUri": file_data[1],
            }
        }
        prompt_structure["contents"][0]["parts"].append(file_part_definition)

    # if self._inline_text:
    #   inline_text_part_definition = {
    #       "inlineData": {
    #           "mimeType": "text/plain",
    #           "data": self._inline_text,
    #       }}
    #   prompt_structure["contents"][0]["parts"].append(
    #       inline_text_part_definition
    #   )

    return json.dumps(prompt_structure, indent=2)


def main():
  prompt_generator = (
      LlmPromptGenerator(
      ).with_prompt(
          "Test Prompt"
      ).with_system_instruction(
          "Test System Instruction"
      ).with_file_data(
          ("text/plain", "gs://test-bucket/test-file.txt")
      ).with_response_schema(
          {"type": "object", "properties": {"test": {"type": "string"}}}
      ).with_temperature(
          0.5
      ).with_max_output_tokens(
          1024
      ).with_response_mime_type(
          "application/json"
      )
  )

  prompt = prompt_generator.build()
  print(prompt)


if __name__ == "__main__":
  main()
