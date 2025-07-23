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
"""Contains classes for managing prompt configs based on the workflow."""

import logging

from prompts.configs import core
from prompts.configs import text
from prompts.configs import video
from socialpulse_common.messages import workflow_execution as wfe


logger = logging.getLogger(__name__)


class PromptConfigFactory:
  """Factory for creating PromptConfig instances."""

  def __init__(self, workflow_exec: wfe.WorkflowExecutionParams):
    self._workflow_exec = workflow_exec

  def get_prompt_config(self) -> core.PromptConfig:
    """Returns the appropriate PromptConfig based on workflow parameters.

    Raises:
      ValueError: If a prompt config cannot be found for the given workflow
        execution parameters.
    """
    source = self._workflow_exec.source
    output = self._workflow_exec.data_output[0]
    prompt_config_cls = None

    if source == wfe.SocialMediaSource.YOUTUBE_VIDEO:
      if output == wfe.SentimentDataType.SENTIMENT_SCORE:
        prompt_config_cls = video.BasicSentimentScoreFromVideoPromptConfig
      elif output == wfe.SentimentDataType.SHARE_OF_VOICE:
        prompt_config_cls = (
            video.ShareOfVoiceSentimentScoresFromVideoPromptConfig
        )
    else:
      prompt_config_cls = text.BasicSentimentScoreFromCommentPromptConfig

    if not prompt_config_cls:
      raise ValueError(
          "Could not find a prompt config for the workflow: "
          f"{str(self._workflow_exec)}"
      )
    return prompt_config_cls(self._workflow_exec)
