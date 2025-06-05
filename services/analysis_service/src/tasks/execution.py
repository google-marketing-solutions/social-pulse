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
from socialpulse_common.messages import workflow_execution_pb2 as wfe
from tasks import core
from tasks import llm_response_processing
from tasks import run_sentiment_job
from tasks import text_prompt
from tasks import video_prompt
from tasks import youtube_comments
from tasks import youtube_data


logger = logging.getLogger(__name__)


SOURCE_TO_TASK_MAPPING = {
    wfe.SocialMediaSource.SOCIAL_MEDIA_SOURCE_YOUTUBE_VIDEO:
        youtube_data.FindYoutubeVideos,
    wfe.SocialMediaSource.SOCIAL_MEDIA_SOURCE_YOUTUBE_COMMENT:
        youtube_comments.FindYoutubeComments
}

SOURCE_TO_PROMPT_GENERATION_TASK_MAPPING = {
    wfe.SocialMediaSource.SOCIAL_MEDIA_SOURCE_YOUTUBE_VIDEO:
        video_prompt.GenerateLlmVideoAnalysisPrompts,
    wfe.SocialMediaSource.SOCIAL_MEDIA_SOURCE_YOUTUBE_COMMENT:
        text_prompt.GenerateLlmTextAnalysisPrompts
}


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


class WorkflowExecution(
    luigi.WrapperTask,
    core.WorkflowExecutionParamsLoaderMixin
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
    starting_task = ExecutionStartTask(execution_id=self.execution_id)
    task_chain = [starting_task]

    content_source = self.workflow_exec.source
    if (
        content_source not in SOURCE_TO_TASK_MAPPING or
        content_source not in SOURCE_TO_PROMPT_GENERATION_TASK_MAPPING
    ):
      raise ValueError(f"Unknown social media source:  {content_source}")

    self._attach_retrieve_content_tasks(task_chain)
    self._attach_analysis_tasks(task_chain)

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
    source = self.workflow_exec.source

    # Add appropriate prompt generation task.
    logger.debug("Looking for prompt generation task for source: %s", source)
    prompt_generation_task_cls = SOURCE_TO_PROMPT_GENERATION_TASK_MAPPING[
        source
    ]

    logger.debug(
        "Instantiating prompt generating task: %s", prompt_generation_task_cls
    )
    prompt_generation_task = prompt_generation_task_cls(
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
