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
"""Migration:  Update workflow status enum values."""

from yoyo import step

__depends__ = {'20250718_01_add_parent_workflow_id'}

steps = [
    step(
        """
        ALTER TABLE public.workflowexecutionparams
            ALTER COLUMN status DROP DEFAULT;
        """
    ),
    step(
        """
        CREATE TYPE workflow_exec_status_enum_new AS ENUM (
            'UNKNOWN',
            'NEW',
            'IN_PROGRESS',
            'COMPLETED',
            'FAILED'
        );
        """
    ),
    step(
        """
        ALTER TABLE public.workflowexecutionparams
            ALTER COLUMN status TYPE workflow_exec_status_enum_new USING
                CASE status
                    WHEN 'STATUS_NEW' THEN 'NEW'::workflow_exec_status_enum_new
                    WHEN 'STATUS_IN_PROGRESS' THEN 'IN_PROGRESS'::workflow_exec_status_enum_new
                    WHEN 'STATUS_COMPLETED' THEN 'COMPLETED'::workflow_exec_status_enum_new
                    -- Add more WHEN clauses here if you had other STATUS_ values like STATUS_UNKNOWN, STATUS_FAILED
                    -- Example: WHEN 'STATUS_UNKNOWN' THEN 'UNKNOWN'::workflow_exec_status_enum_new
                    ELSE 'UNKNOWN'::workflow_exec_status_enum_new -- Fallback for any unexpected old values
                END;
        """
    ),
    step(
        """
        ALTER TABLE public.workflowexecutionparams
        ALTER COLUMN status SET DEFAULT 'NEW'::workflow_exec_status_enum_new;
        """
    )
]
