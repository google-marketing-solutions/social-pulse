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
"""Migration:  Add the last completed task col to WorkflowExecutionParams."""

from yoyo import step

__depends__ = {'20250418_01_create_workflow_execution_params'}

steps = [
    step(
        """
        CREATE TYPE public.workflow_exec_status_enum AS ENUM (
            'STATUS_NEW',
            'STATUS_IN_PROGRESS',
            'STATUS_COMPLETED'
        );
        """,
        """"
        DROP TYPE public.workflow_exec_status_enum
        """
    ),
    step(
        """
        ALTER TABLE WorkflowExecutionParams
            ADD COLUMN status public.workflow_exec_status_enum NOT NULL DEFAULT 'STATUS_NEW',
            ADD COLUMN lastCompletedTask TEXT,
            ADD COLUMN createdOn TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            ADD COLUMN lastUpdatedOn TIMESTAMPTZ NOT NULL DEFAULT NOW();
        """,
        """
        ALTER TABLE WorkflowExecutionParams
            DROP COLUMN status,
            DROP COLUMN lastCompletedTask,
            DROP COLUMN createdOn,
            DROP COLUMN lastUpdatedOn;
        """
    )
]
