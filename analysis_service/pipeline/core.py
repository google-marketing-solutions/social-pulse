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
"""Base classes for setting up a pipeline."""


import abc
import pandas as pd

from socialpulse.common.valueobjects import report


class AnalysisStep(abc.ABC):
  """Interface class for a  pipeline analysis step.

  An AnalysisStep represents a single and discreet unit of work that needs to
  be executed as part of a pipeline.

  Subclasses should implement the `execute` method.
  """

  def __init__(self, report_params: report.ReportParameters):
    """Constructor for the AnalysisStep.

    Args:
      report_params: The parameters the report was configured with.
    """
    self.report_params = report_params

  @abc.abstractmethod
  def execute(self, data: pd.DataFrame) -> pd.DataFrame:
    """Executes the logic this sentiment analysis step encapsulates.

    Args:
      data: The input data for the analysis step.

    Returns:
      The output data after the sentiment analysis step has been executed.
    """
    pass
