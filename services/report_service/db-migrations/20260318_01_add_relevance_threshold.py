#  Copyright 2026 Google LLC
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
"""Migration: Add relevance threshold to SentimentReports."""

from yoyo import step

__depends__ = {"20260217_01_add_include_justifications_column"}

steps = [
    step(
        """
        ALTER TABLE SentimentReports
            ADD COLUMN relevanceThreshold INTEGER NOT NULL DEFAULT 90
        """,
        "ALTER TABLE SentimentReportsDROP COLUMN relevanceThreshold"
    )
]
