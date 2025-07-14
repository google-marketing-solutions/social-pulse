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
"""Contains classes for prompt configs."""
import abc
import copy

import pandas as pd
from socialpulse_common.messages import workflow_execution_pb2 as wfe


LLM_REQUEST_COL_NAME = "request"


SHARE_OF_VOICE_WEIGHT_RESPONSE_SCHEMA_MIXIN: dict[str, str] = {
    "weight": {"type": "number"}
}


JUSTIFICATION_RESPONSE_SCHEMA_MIXIN: dict[str, str] = {
    "justifications": {
        "type": "array",
        "items": {
            "type": "string",
        },
    }
}


class SentimentResponseSchemaBuilder:
  """Builds the JSON schema for sentiment analysis responses.

  This builder sets up a base schema for sentiment analysis, including
  properties for 'summary' and an array of 'sentiments'. Each sentiment
  item defaults to 'productOrBrand', 'sentimentScore', and 'relevanceScore'.
  """

  BASE_SENTIMENT_RESPONSE_SCHEMA: dict[str, str] = {
      "type": "object",
      "properties": {
          "summary": {"type": "string"},
          "sentiments": {
              "type": "array",
              "items": {
                  "type": "object",
                  "properties": {},
              }
          }
      }
  }

  def __init__(self):
    """Initializes the SentimentResponseSchemaBuilder.

    Sets up the default properties for each sentiment item:
    - 'productOrBrand': type 'string'
    - 'sentimentScore': type 'number'
    - 'relevanceScore': type 'number'

    These can be extended using the `add_property` method.
    """
    self._properties = {
        "productOrBrand": {"type": "string"},
        "sentimentScore": {"type": "number"},
        "relevanceScore": {"type": "number"}
    }

  def add_property(
      self,
      prop: dict[str, str]
  ) -> "SentimentResponseSchemaBuilder":
    """Adds additional properties to the sentiment item schema.

    Args:
      prop: A dictionary representing the properties to add. Example:
        `{"newProperty": {"type": "string"}}`
    Returns:
      The SentimentResponseSchemaBuilder instance for method chaining.
    """
    self._properties.update(prop)
    return self

  def build(self) -> dict[str, str]:
    """Constructs and returns the final JSON schema.

    Returns:
      A dictionary representing the complete JSON schema for sentiment
      analysis responses.
    """
    schema = copy.deepcopy(self.BASE_SENTIMENT_RESPONSE_SCHEMA)
    schema["properties"]["sentiments"]["items"]["properties"].update(
        self._properties
    )
    return schema


class PromptConfig(abc.ABC):
  """Abstract base class for prompt configurations.

  Prompt configurations are used to customize the generation of a prommpt based
  on the workflow execution parameters.  Based on the content type and report
  type, a configuration provides the details on what input columns are needed,
  the system instructions, the base prompt
  """

  def __init__(self, workflow_exec: wfe.WorkflowExecutionParams):
    self._workflow_exec = workflow_exec

  @abc.abstractmethod
  def get_input_columns(self) -> list[str]:
    """Returns the list of expected input DataFrame columns."""
    pass

  @abc.abstractmethod
  def get_system_instruction(self) -> str:
    """Returns the system instruction for the LLM."""
    pass

  @abc.abstractmethod
  def generate_llm_prompt(self, row: pd.Series) -> str:
    """Generates the base prompt string for the LLM."""
    pass

  @abc.abstractmethod
  def get_file_data(self, row: pd.Series) -> list[tuple[str, str]] | None:
    """Returns file data for the LLM, if any."""
    return None

  @abc.abstractmethod
  def get_response_schema(self) -> str:
    """Returns the response schema for the LLM."""
    return None
