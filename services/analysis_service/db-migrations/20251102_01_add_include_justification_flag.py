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
"""Migration: Add include justifications flag to workflow executions."""

from yoyo import step

__depends__ = {'20250903_01_add_report_id'}

steps = [
    step(
        """
        ALTER TABLE public.workflowexecutionparams
        ADD COLUMN includeJustifications BOOLEAN NOT NULL DEFAULT TRUE;
        """,
        """
        ALTER TABLE public.workflowexecutionparams
        DROP COLUMN includeJustifications;
        """
    )
]
