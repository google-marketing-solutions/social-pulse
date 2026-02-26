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
"""Module for Analysis Results core interfaces."""

import abc
from domain import sentiment_report
from socialpulse_common.messages import analysis_result


class ResultDataBuilder(abc.ABC):
  """Abstract base class for all analysis result builders."""

  @abc.abstractmethod
  def build(
      self,
      report_entity: sentiment_report.SentimentReportEntity,
      start_date: str | None = None,
      end_date: str | None = None,
      channel_title: str | None = None,
      excluded_channels: list[str] | None = None,
  ) -> analysis_result.BaseAnalysisResultSet | None:
    """Builds an individual analysis result set.

    Responsible for building an individual analysis result set, to be added
    to the overall analysis results.

    Args:
      report_entity: The sentiment report entity.
      start_date: Optional start date filter.
      end_date: Optional end date filter.
      channel_title: Optional channel title filter.
      excluded_channels: Optional list of channels to exclude.

    Returns:
      The analysis result set.
    """
    pass
