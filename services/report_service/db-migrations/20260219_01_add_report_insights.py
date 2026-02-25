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
"""Migration: Create the ReportInsights table."""

from yoyo import step

__depends__ = {'20250729_01_add_reports_table'}

steps = [
    step(
        """
        CREATE TYPE public.report_insight_type_enum AS ENUM (
            'TREND',
            'SPIKE'
        );
        """,
        """
        DROP TYPE public.report_insight_type_enum
        """),
    step(
        """
        CREATE TABLE ReportInsights (
            reportInsightId UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            reportId UUID NOT NULL,
            insightType public.report_insight_type_enum NOT NULL,
            content JSONB NOT NULL,
            rawPromptOutput TEXT,
            createdOn TIMESTAMPTZ NOT NULL DEFAULT NOW(),

            CONSTRAINT fk_report_insights_report_id
                FOREIGN KEY (reportId)
                REFERENCES SentimentReports (reportId)
                ON DELETE CASCADE
        );
        """,
        """
        DROP TABLE ReportInsights;
        """),
    step(
        """
        CREATE INDEX idx_report_insights_report_id ON ReportInsights (reportId);
        """,
        """
        DROP INDEX idx_report_insights_report_id;
        """
    )
]
