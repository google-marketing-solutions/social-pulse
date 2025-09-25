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


class WorkflowExecutionTrigger(service.RegisterableService, abc.ABC):
  """Abstract interface for triggering a workflow execution pipeline."""

  @abc.abstractmethod
  def trigger_workflow(self, execution_id: str) -> None:
    """Triggers the execution of a specific workflow.

    Args:
        execution_id: The unique ID of the workflow to execute.
    """
    raise NotImplementedError
