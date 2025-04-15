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
"""Module for core sentiment analysis task classes/enums."""

import abc

import luigi
from socialpulse_common import service
from socialpulse_common.messages import workflow_execution_pb2 as wfe


class WorkflowExecutionLoaderService(service.RegisterableService):
  """Service for loading workflow execution parameters."""

  @abc.abstractmethod
  def load_execution(self) -> wfe.WorkflowExecutionParams:
    pass


class SentimentTask(luigi.Task, abc.ABC):
  """Abstract class representing a sentiment analysis task.

  Subclasses should implement the `requires`, `output` and `run` methods.
  """
  execution_id = luigi.Parameter()

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    workflow_exec_loader_service = service.registry.get(
        WorkflowExecutionLoaderService
    )
    self.workflow_exec: wfe.WorkflowExecutionParams = (
        workflow_exec_loader_service.load_execution(self.execution_id)
    )

  @abc.abstractmethod
  def run(self) -> None:
    pass

  @abc.abstractmethod
  def requires(self) -> luigi.Task:
    pass

  @abc.abstractmethod
  def output(self) -> luigi.Target:
    pass
