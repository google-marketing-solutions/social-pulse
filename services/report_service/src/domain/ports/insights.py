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

"""Module defining the InsightsProvider port."""

import abc
import typing


class InsightsProvider(abc.ABC):
    """Protocol for providers that generate insights from report data."""

    @abc.abstractmethod
    def generate_base_insights(
        self, report_context: str
    ) -> tuple[dict[str, typing.Any], str]:
        """Generates base insights (top trends) from the report context.

        Args:
            report_context (str): The full context of the report data.

        Returns:
            tuple[dict, str]: A tuple containing the parsed JSON insights
                and the raw response string.
        """

    @abc.abstractmethod
    def generate_spike_analysis(
        self, report_context: str
    ) -> tuple[dict[str, typing.Any], str]:
        """Generates spike analysis from the report context.

        Args:
            report_context (str): The full context of the report data.

        Returns:
            tuple[dict, str]: A tuple containing the parsed JSON spike
                analysis and the raw response string.
        """

    @abc.abstractmethod
    def answer_chat_query(
        self,
        report_context: str,
        chat_history: list[dict[str, typing.Any]],
        query: str,
    ) -> str:
        """Answers a user chat query based on the report context and history.

        Args:
            report_context (str): The full context of the report data.
            chat_history (list[dict]): List of previous chat messages.
            query (str): The current user query.

        Returns:
            str: The conversational response.
        """

