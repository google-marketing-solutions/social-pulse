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

import pandas as pd
from socialpulse_common.messages import workflow_execution_pb2 as wfe


LLM_REQUEST_COL_NAME = "request"


BASE_SENTIMENT_RESPONSE_SCHEMA: dict[str, str] = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "productOrBrand": {"type": "string"},
            "summary": {"type": "string"},
            "sentimentScore": {"type": "number"},
            "relevanceScore": {"type": "number"}
        },
    },
}


JUSTIFICATION_RESPONSE_SCHEMA: dict[str, str] = {
    "justifications": {
        "type": "array",
        "items": {
            "type": "string",
        },
    }
}


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
