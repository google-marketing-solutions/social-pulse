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
import unittest
from unittest import mock

import sentiment_task_mixins as test_mixins
from tasks import cleanup
from tasks import constants


class CleanupTaskTest(
    unittest.TestCase, test_mixins.SetupMockSentimentTaskDepependenciesMixin
):
  def setUp(self):
    super().setUp()
    self.setup_all_mock_dependencies()
    self.my_required_task = mock.Mock()
    self.my_required_task.output.return_value.table_name = (
        "last_task_output"
    )

  def test_dataset_name_property(self):
    """Tests that the dataset_name property returns the correct name.

    Given a CleanupTask initialized with an execution ID.
    When the dataset_name property is accessed.
    Then the returned dataset name includes the
    SENTIMENT_RESULTS_DATASET_PREFIX and the execution ID.
    """
    # Arrange
    task = cleanup.CleanupTask(
        execution_id="test_execution_id",
        my_required_task=self.my_required_task,
    )

    # Act
    dataset_name = task.dataset_name

    # Assert
    expected_name = (
        f"{constants.SENTIMENT_RESULTS_DATASET_PREFIX}_test_execution_id"
    )
    self.assertEqual(dataset_name, expected_name)

  def test_run_copies_data(self):
    """Tests that data is copied from the source to the target repo.

    Given a CleanupTask initialized with an execution ID
    When the run method is invoked.
    Then the sentiment data repository's is copied from the source to the target
      repo.
    """
    # Arrange
    task = cleanup.CleanupTask(
        execution_id="test_execution_id",
        my_required_task=self.my_required_task,
    )

    # Act
    task.run()

    # Assert
    self.mock_sentiment_data_repo.copy_sentiment_data.assert_called_once_with(
        "last_task_output",
        f"{constants.SENTIMENT_RESULTS_DATASET_PREFIX}_test_execution_id",
    )


if __name__ == "__main__":
  unittest.main()
