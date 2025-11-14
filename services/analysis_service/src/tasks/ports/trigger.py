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
"""Module for the abstract interface (Port) for triggering workflows."""

import abc
from socialpulse_common import service
from socialpulse_common.messages import sentiment_report as report_msg


class WorkflowExecutionTrigger(service.RegisterableService, abc.ABC):
  """Abstract interface for triggering a workflow execution pipeline."""

  @abc.abstractmethod
  def trigger_workflow(self, execution_id: str) -> None:
    """Triggers the execution of a specific workflow.

    Args:
        execution_id: The unique ID of the workflow to execute.
    """
    raise NotImplementedError


class ReportCompletionService(service.RegisterableService, abc.ABC):
  """Abstract interface for marking reports as completed."""

  @abc.abstractmethod
  def mark_report_completed(
      self, report_id: str, datasets: list[report_msg.SentimentReportDataset]
  ) -> None:
    """Marks a report as completed.

    Args:
        report_id: The unique ID of the report to mark as completed.
        datasets: A list of SentimentReportDataset objects associated with the
          completed report.
    """
    raise NotImplementedError
