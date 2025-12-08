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

import sentiment_task_mixins as test_mixins
from tasks import constants
from tasks import load_parent_data


class LoadParentWorkflowDatasetTaskTest(
    unittest.TestCase,
    test_mixins.SetupMockSentimentTaskDepependenciesMixin
):
  def setUp(self):
    super().setUp()
    self.setup_all_mock_dependencies()
    self.mock_execution_params.parent_execution_id = "parent_exec_id"

  def test_run_copies_data(self):
    """Tests that data is copied from the source to the target repo.

    Given a LoadParentWorkflowDatasetTask initialized with an execution ID
    When the run method is invoked.
    Then sentiment data is copied from the correct source (parent) to the
      target (current) dataset names.
    """
    # Arrange
    task = load_parent_data.LoadParentWorkflowDatasetTask(
        execution_id="test_execution_id",
        my_required_task=self.mock_required_task,
    )

    # Act
    task.run()

    # Assert
    expected_source_table = (
        f"{constants.SENTIMENT_RESULTS_DATASET_PREFIX}_parent_exec_id"
    )
    self.mock_sentiment_data_repo.copy_sentiment_data.assert_called_once_with(
        expected_source_table,
        task.dataset_name,
    )


if __name__ == "__main__":
  unittest.main()
