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
"""Module with service implementations required by the tasks."""

import datetime

from socialpulse_common.messages import workflow_execution_pb2 as wfe
from tasks import core


class StubWorkflowExecutionLoaderService(core.WorkflowExecutionLoaderService):
  """Stub implementation of the WorkflowExecutionLoaderService.

  This class provides a stubbed implementation for loading workflow executions.
  """

  def load_execution(self, execution_id: str) -> wfe.WorkflowExecutionParams:
    """Loads a workflow execution by its ID.

    This method provides a stubbed implementation for loading a workflow
    execution. It returns a pre-defined WorkflowExecution object with
    sample data.

    Args:
      execution_id: The ID of the workflow execution to load.
    Returns:
      A WorkflowExecution object.
    """
    stubbed_workflow_exec = wfe.WorkflowExecutionParams()
    stubbed_workflow_exec.executionId = execution_id
    stubbed_workflow_exec.source = (
        wfe.SocialMediaSource.SOCIAL_MEDIA_SOURCE_YOUTUBE_VIDEO
    )
    stubbed_workflow_exec.data_outputs.append([
        wfe.SentimentDataType.SENTIMENT_DATA_TYPE_SENTIMENT_ANALYSIS,
        wfe.SentimentDataType.SENTIMENT_DATA_TYPE_DISTRIBUTION
    ])

    stubbed_workflow_exec.topic_type = wfe.TopicType.TOPIC_TYPE_PRODUCT
    stubbed_workflow_exec.topic = "product"

    stubbed_workflow_exec.start_time = datetime.datetime.now()
    stubbed_workflow_exec.end_time = datetime.datetime.now()

    return stubbed_workflow_exec
