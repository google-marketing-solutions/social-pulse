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
"""Migration: Add exported status to workflow executions status."""

from yoyo import step

__depends__ = {"20251102_01_add_include_justification_flag"}

steps = [
    step(
        "ALTER TYPE workflow_exec_status_enum_new ADD VALUE 'EXPORTED';",
        "",  # There is no way to remove a enum value once added.
    )
]
