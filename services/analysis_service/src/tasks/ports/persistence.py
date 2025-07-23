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
"""Module for workflow related service interfaces/abstract classes."""

import abc

import pandas as pd
from socialpulse_common import service
from socialpulse_common.messages import workflow_execution as wfe


class WorkflowExecutionPersistenceService(service.RegisterableService):
  """Service for creating, reading, and updating workflow execution parameters.

  This service provides an interface for retrieving workflow execution
  parameters based on a given execution ID.  It also provides functions for
  creating and updating workflow execution parameters.
  """

  @abc.abstractmethod
  def load_execution(self, execution_id: str) -> wfe.WorkflowExecutionParams:
    """Loads workflow execution parameters.

    Args:
      execution_id: The ID of the workflow execution.

    Returns:
      The workflow execution parameters.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def create_execution(
      self,
      execution_params: wfe.WorkflowExecutionParams
  ) -> None:
    """Saves workflow execution parameters.

    Args:
      execution_params: The workflow execution parameters.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def mark_last_completed_task(
      self,
      execution_id: str,
      task_name: str
  ) -> None:
    """Marks the last completed task for a workflow execution.

    Args:
      execution_id: The ID of the workflow execution.
      task_name: The name of the task that was completed.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def update_status(
      self,
      execution_id: str,
      status: wfe.Status
  ) -> None:
    """Updates the status of a workflow execution.

    Args:
      execution_id: The ID of the workflow execution.
      status: The new status of the workflow execution.
    """
    raise NotImplementedError


class SentimentDataRepo(service.RegisterableService, abc.ABC):
  """Service for reading/writing data to the sentiment data set repo.

  This service provides an interface for interacting with a data repository
  that stores sentiment analysis data sets. It allows loading and writing
  sentiment data in the form of pandas DataFrames.
  """

  @abc.abstractmethod
  def exists(self, dataset_name: str) -> bool:
    """Checks if a sentiment data set exists in the specified table.

    Args:
      dataset_name: The name of the data set to check for existence.

    Returns:
      True if the table exists, False otherwise.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def load_sentiment_data(self, dataset_name: str) -> pd.DataFrame:
    """Loads a sentiment data set from the specified table.

    Args:
      dataset_name: The name of the data set to load data from.

    Returns:
      A pandas DataFrame containing the sentiment data.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def write_sentiment_data(
      self,
      dataset_name: str,
      sentiment_dataset: pd.DataFrame
  ) -> None:
    """Writes the provided data set to the specified sentiment data set.

    Args:
      dataset_name: The name of the table to write data to.
      sentiment_dataset: The pandas DataFrame containing the sentiment data to
        write.
    """
    raise NotImplementedError

  def copy_sentiment_data(
      self,
      source_dataset_name: str,
      target_dataset_name: str
  ) -> None:
    """Copies a sentiment data set to a provided name.

    Args:
      source_dataset_name: The name of the data set to copy from.
      target_dataset_name: The name of the new data set to create.
    """
    raise NotImplementedError
