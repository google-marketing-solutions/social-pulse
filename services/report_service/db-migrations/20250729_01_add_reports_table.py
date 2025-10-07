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
"""Migration:  Create the SentimentReports table."""

from yoyo import step

__depends__ = {}

steps = [
    step(
        """
        CREATE TYPE public.sentiment_report_status_enum AS ENUM (
            'NEW',
            'IN_PROGRESS',
            'COMPLETED',
            'FAILED'
        );
        """, """
        DROP TYPE public.sentiment_report_status_enum
        """),
    step(
        """
        CREATE TABLE SentimentReports (
            reportId UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            sources TEXT[] NOT NULL,
            dataOutputs TEXT[] NOT NULL,
            topic TEXT NOT NULL,
            dateRangeStart TIMESTAMP NOT NULL,
            dateRangeEnd TIMESTAMP NOT NULL,
            status public.sentiment_report_status_enum NOT NULL DEFAULT 'NEW',
            createdOn TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            lastUpdatedOn TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """, "DROP TABLE SentimentReports"),
    step(
        """
        CREATE TABLE SentimentReportDatasets (
            reportDatasetId UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            reportId UUID NOT NULL,
            source TEXT NOT NULL,
            dataOutput TEXT NOT NULL,
            outputUri TEXT NOT NULL,

            CONSTRAINT fk_parent_sentiment_report_id
                FOREIGN KEY (reportId)
                REFERENCES SentimentReports (reportId)
        )
        """, "DROP TABLE SentimentReportDatasets")
]
