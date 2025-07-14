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

import luigi
from socialpulse_common import service
from socialpulse_common.messages import workflow_execution_pb2 as wfe
from tasks import core as task_core
from tasks import generate_prompt
from tasks import llm_response_processing
from tasks import run_sentiment_job
from tasks import youtube_comments
from tasks import youtube_data
from tasks.ports import persistence


logger = logging.getLogger(__name__)


SOURCE_TO_TASK_MAPPING = {
    wfe.SocialMediaSource.SOCIAL_MEDIA_SOURCE_YOUTUBE_VIDEO:
        youtube_data.FindYoutubeVideos,
    wfe.SocialMediaSource.SOCIAL_MEDIA_SOURCE_YOUTUBE_COMMENT:
        youtube_comments.FindYoutubeComments
}


@task_core.SentimentTask.event_handler(luigi.Event.SUCCESS)
def handle_task_complete(sentiment_task: task_core.SentimentTask) -> None:
  """Handles a SentimentTask completion event.

  This function is triggered when a task inheriting from
  `task_core.SentimentTask` successfully completes. It logs the completion and
  updates the workflow execution state in the persistence layer.

  Args:
    sentiment_task: The completed SentimentTask instance.
  """
  task_name = sentiment_task.get_task_family()
  workflow_exec_id = sentiment_task.workflow_exec.execution_id
  logger.info(
      "Marking task '%s' as complete for workflow execution '%s.",
      task_name,
      workflow_exec_id
  )

  workflow_exec_repo = service.registry.get(
      persistence.WorkflowExecutionPersistenceService
  )
  workflow_exec_repo.mark_last_completed_task(workflow_exec_id, task_name)


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


class ExecutionFinishTask(
    luigi.Task,
    task_core.WorkflowExecutionParamsLoaderMixin
):
  """Represents the end of a sentiment analysis workflow execution.

  This task is responsible for logging the end of a workflow execution, as well
  as setting the finished status on the workflow execution.
  """

  task_namespace = "execution"

  execution_id = luigi.Parameter()

  # Task to run as the requirement for this task (non-significant param)
  my_required_task = luigi.TaskParameter(significant=False)

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.load_workflow_execution_params(self.execution_id)
    self._has_completed = False

  def requires(self) -> luigi.Task:
    """Specifies the required task for this task.

    The dependency is determined by the `my_required_task` parameter, which is
    set when the task is instantiated.

    Returns:
      A luigi.Task instance representing the required task.
    """
    if not self.my_required_task:
      return  []
    else:
      return self.my_required_task

  def run(self):
    logging.info("Finishing workflow execution '%s'", self.execution_id)
    workflow_persistence_srv = service.registry.get(
        persistence.WorkflowExecutionPersistenceService
    )

    workflow_persistence_srv.update_status(
        self.execution_id,
        wfe.Status.STATUS_COMPLETED
    )
    self._has_completed = True

  def complete(self):
    return self._has_completed


class WorkflowExecution(
    luigi.WrapperTask,
    task_core.WorkflowExecutionParamsLoaderMixin
):
  """Represents a workflow execution.

  This task is a wrapper task that orchestrates the execution of a series of
  sentiment analysis tasks. It defines the order in which the tasks should be
  executed and ensures that the required dependencies are met.
  """

  task_namespace = "execution"

  # Uniquely identifies the workflow execution this task is working in.
  execution_id = luigi.Parameter()

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.load_workflow_execution_params(self.execution_id)

  def requires(self):
    """Specifies the required tasks for this workflow execution.

    This method defines the order in which the tasks should be executed.
    It returns a list of tasks that need to be completed before the workflow
    execution can be considered complete.

    Yields:
      The workflow execution task chain.
    """
    if self.workflow_exec.status == wfe.Status.STATUS_COMPLETED:
      logger.info(
          "Workflow execution '%s' is already completed, stopping execution.",
          self.execution_id
      )
      return []

    workflow_persistence_srv = service.registry.get(
        persistence.WorkflowExecutionPersistenceService
    )

    content_source = self.workflow_exec.source
    if (content_source not in SOURCE_TO_TASK_MAPPING):
      workflow_persistence_srv.update_status(
          self.execution_id,
          wfe.Status.STATUS_FAILED
      )
      raise ValueError(f"Unknown social media source:  {content_source}")

    starting_task = ExecutionStartTask(execution_id=self.execution_id)
    task_chain = [starting_task]

    self._attach_retrieve_content_tasks(task_chain)
    self._attach_analysis_tasks(task_chain)

    if self.workflow_exec.last_completed_task_id:
      logger.info(
          "Restarting workflow execution '%s' from task '%s'",
          self.execution_id,
          self.workflow_exec.last_completed_task_id
      )
      task_chain = self._prune_completed_tasks_from_chain(
          task_chain,
          self.workflow_exec.last_completed_task_id
      )

    last_task_in_chain = task_chain[-1]
    finishing_task = ExecutionFinishTask(
        my_required_task=last_task_in_chain,
        execution_id=self.execution_id
    )
    task_chain.append(finishing_task)

    logger.debug("Workflow execution task chain: %s", task_chain)
    yield task_chain

  def _attach_retrieve_content_tasks(self, task_chain: list[luigi.Task]):
    """Attaches content retrieval tasks to the task chain.

    Args:
      task_chain: The task chain to attach the retrieval tasks to.
    """
    last_task_in_chain = task_chain[-1]
    source = self.workflow_exec.source
    logger.debug("Looking for content retrieve tasks for source: %s", source)

    if (
        source == wfe.SocialMediaSource.SOCIAL_MEDIA_SOURCE_YOUTUBE_VIDEO or
        source == wfe.SocialMediaSource.SOCIAL_MEDIA_SOURCE_YOUTUBE_COMMENT
    ):
      video_gather_task_cls = SOURCE_TO_TASK_MAPPING[
          wfe.SocialMediaSource.SOCIAL_MEDIA_SOURCE_YOUTUBE_VIDEO
      ]
      video_gather_task = video_gather_task_cls(
          execution_id=self.execution_id,
          my_required_task=last_task_in_chain
      )
      task_chain.append(video_gather_task)

      if source == wfe.SocialMediaSource.SOCIAL_MEDIA_SOURCE_YOUTUBE_COMMENT:
        comment_gather_task_cls = SOURCE_TO_TASK_MAPPING[
            wfe.SocialMediaSource.SOCIAL_MEDIA_SOURCE_YOUTUBE_COMMENT
        ]
        comment_gather_task = comment_gather_task_cls(
            execution_id=self.execution_id,
            my_required_task=video_gather_task
        )
        task_chain.append(comment_gather_task)

  def _attach_analysis_tasks(self, task_chain: list[luigi.Task]):
    """Attaches data prep and analysis tasks to the task chain.

    Args:
      task_chain: The task chain to attach the analysis tasks to.
    """
    last_task_in_chain = task_chain[-1]

    # Add appropriate prompt generation task.
    prompt_generation_task = generate_prompt.GenerateLlmPromptForContentTask(
        execution_id=self.execution_id,
        my_required_task=last_task_in_chain
    )
    task_chain.append(prompt_generation_task)

    # Add LLM job execution and response processing tasks.
    llm_job_task = run_sentiment_job.RunSentimentAnalysisJobTask(
        execution_id=self.execution_id,
        my_required_task=prompt_generation_task
    )
    task_chain.append(llm_job_task)

    process_response_task = (
        llm_response_processing.ProcessLlmSentimentResponses(
            execution_id=self.execution_id,
            my_required_task=llm_job_task
        )
    )
    task_chain.append(process_response_task)

  def _prune_completed_tasks_from_chain(
      self,
      task_chain: list[task_core.SentimentTask],
      last_completed_task: str
  ) -> list[task_core.SentimentTask]:
    """Prunes completed tasks from the task chain.

    Finds the last completed task in the task chain, and then prunes it and all
    preceding tasks from the chain.

    Args:
      task_chain: The task chain to prune completed tasks from.
      last_completed_task: The task family name of the last completed task.
    Returns:
      Task chain (list of SentimentTasks) pruned of completed tasks.
    """
    for i, task in enumerate(task_chain):
      if task.get_task_family() == last_completed_task:
        return task_chain[i + 1:]
    else:
      logger.info(
          "Last completed task '%s' not found in chain, so restarting from "
          "beginning",
          last_completed_task
      )
      return task_chain
