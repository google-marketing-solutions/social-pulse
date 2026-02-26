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
"""Message classes for analysis results."""

from typing import List, Optional
import pydantic
from pydantic.alias_generators import to_camel


class BaseAnalysisResultSet(pydantic.BaseModel):
  """Base class that all analysis results extend."""

  model_config = pydantic.ConfigDict(
      populate_by_name=True,
      alias_generator=to_camel,
  )


class SentimentDataPoint(BaseAnalysisResultSet):
  date: str
  positive: int
  negative: int
  neutral: int


class SentimentOverTimeResultSet(BaseAnalysisResultSet):
  sentiment_over_time: List[SentimentDataPoint]


class OverallSentimentDataPoint(BaseAnalysisResultSet):
  positive: int
  negative: int
  neutral: int
  item_count: Optional[int] = None


class OverallSentimentResultSet(BaseAnalysisResultSet):
  overall_sentiment: OverallSentimentDataPoint


class JustificationCategoryDataPoint(BaseAnalysisResultSet):
  category: str
  count: int


class JustificationBreakdown(BaseAnalysisResultSet):
  positive: List[JustificationCategoryDataPoint] = pydantic.Field(
      default_factory=list)
  negative: List[JustificationCategoryDataPoint] = pydantic.Field(
      default_factory=list)
  neutral: List[JustificationCategoryDataPoint] = pydantic.Field(
      default_factory=list)


class JustificationBreakdownResultSet(BaseAnalysisResultSet):
  justification_breakdown: JustificationBreakdown


class ShareOfVoiceDataPoint(BaseAnalysisResultSet):
  name: str
  positive: int
  negative: int
  neutral: int


class ShareOfVoiceResultSet(BaseAnalysisResultSet):
  share_of_voice: List[ShareOfVoiceDataPoint]


class SourceAnalysisResult(BaseAnalysisResultSet):
  sentiment_over_time: Optional[List[SentimentDataPoint]] = None
  overall_sentiment: Optional[OverallSentimentDataPoint] = None
  justification_breakdown: Optional[JustificationBreakdown] = None
  share_of_voice: Optional[List[ShareOfVoiceDataPoint]] = None
