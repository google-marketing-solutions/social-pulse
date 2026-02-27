#  Copyright 2026 Google LLC
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
"""Module for Report Insights dataclasses and enums."""

import datetime
import enum
import typing

import pydantic
from pydantic import alias_generators


class InsightType(enum.StrEnum):
  """Types of insights that can be generated for a sentiment report."""
  TREND = "TREND"
  SPIKE = "SPIKE"


class ReportInsight(pydantic.BaseModel):
  """Represents a generated insight for a sentiment report."""
  model_config = pydantic.ConfigDict(
      use_enum_names=True,
      populate_by_name=True,
      alias_generator=alias_generators.to_camel,
  )

  # Unique identifier for the insight
  insight_id: typing.Optional[str] = None

  # ID of the report this insight belongs to
  report_id: str

  # The type of insight
  insight_type: InsightType

  # The generated JSON content
  content: typing.Dict[str, typing.Any]

  # The raw text output from the LLM prompt
  raw_prompt_output: typing.Optional[str] = None

  # Timestamp of when this insight was created
  created_on: typing.Optional[datetime.datetime] = None


class ChatMessage(pydantic.BaseModel):
  """Represents a single message in a chat conversation."""
  model_config = pydantic.ConfigDict(
      use_enum_names=True,
      populate_by_name=True,
      alias_generator=alias_generators.to_camel,
  )

  role: str
  content: str


class ChatRequest(pydantic.BaseModel):
  """Represents a request to chat about a report."""
  model_config = pydantic.ConfigDict(
      use_enum_names=True,
      populate_by_name=True,
      alias_generator=alias_generators.to_camel,
  )

  query: str
  history: list[ChatMessage] = pydantic.Field(default_factory=list)


class ChatResponse(pydantic.BaseModel):
  """Represents a response from a chat query."""
  model_config = pydantic.ConfigDict(
      use_enum_names=True,
      populate_by_name=True,
      alias_generator=alias_generators.to_camel,
  )

  response: str
