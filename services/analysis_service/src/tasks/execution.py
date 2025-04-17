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
"""Module for chaining sentiment analysis tasks together."""
import logging

from infrastructure.persistence.stubbed import workflow_data_repo as wdr
import luigi
from socialpulse_common import service
from tasks import ports


log_format = (
    "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
logging.basicConfig(level=logging.DEBUG, format=log_format)


class ExecutionStartTask(luigi.Task):
  """Represents the start of a sentiment analysis workflow execution.

  This task is responsible for logging the start of a workflow execution.
  It takes an execution ID as a parameter to identify the specific workflow.
  """

  task_namespace = "execution"

  execution_id = luigi.Parameter()

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._has_completed = False

  def run(self):
    logging.info("Starting workflow execution '%s'", self.execution_id)
    self._has_completed = True

  def complete(self):
    return self._has_completed


class WorkflowExecution(luigi.WrapperTask):
  """Represents a workflow execution.

  This task is a wrapper task that orchestrates the execution of a series of
  sentiment analysis tasks. It defines the order in which the tasks should be
  executed and ensures that the required dependencies are met.
  """

  task_namespace = "execution"

  # Uniquely identifies the workflow execution this task is working in.
  execution_id = luigi.Parameter()

  def requires(self):
    """Specifies the required tasks for this workflow execution.

    This method defines the order in which the tasks should be executed.
    It returns a list of tasks that need to be completed before the workflow
    execution can be considered complete.

    Yields:
      The workflow execution task chain.
    """
    starting_task = ExecutionStartTask(execution_id=self.execution_id)

    # Below is an example of how this WorkflowExecution task should be used,
    # where tasks are created and linked to each other
    #
    # task_a = TaskA(
    #     execution_id=self.execution_id,
    #     my_required_task=starting_task
    # )
    # task_b = TaskB(
    #     execution_id=self.execution_id,
    #     my_required_task=task_a
    # )
    # yield [starting_task, task_a, task_b]

    yield [starting_task]


if __name__ == "__main__":
  print("################# Firing off workflow exeuciton... ###############")

  service.registry.register(
      ports.persistence.WorkflowExecutionLoaderService,
      wdr.StubWorkflowExecutionLoaderService()
  )

  run_result = luigi.build(
      [WorkflowExecution(execution_id="some_execution_id")],
      detailed_summary=True,
      local_scheduler=True
  )

  print("################# Workflow execution complete! ###############")
