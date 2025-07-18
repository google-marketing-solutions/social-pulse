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
#
# pylint: disable=invalid-name
"""Migration:  Add parent execution id to WorkflowExecutionParams."""

from yoyo import step

__depends__ = {'20250609_01_add_status_tracking_columns'}

steps = [
    step(
        """
        ALTER TABLE WorkflowExecutionParams
            ADD COLUMN parentExecutionId UUID;
        """,
        """
        ALTER TABLE WorkflowExecutionParams
            DROP COLUMN parentWorkflowId;
        """
    ),
    step(
        """
        ALTER TABLE WorkflowExecutionParams
            ADD CONSTRAINT fk_parent_workflow_id
            FOREIGN KEY (parentExecutionId)
            REFERENCES WorkflowExecutionParams (executionId)
        """,
        """
        ALTER TABLE WorkflowExecutionParams
            DROP CONSTRAINT fk_parent_workflow_id;
        """
    )
]
