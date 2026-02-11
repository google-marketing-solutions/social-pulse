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
"""Module for dataset persistence interface."""

import abc
import typing

from socialpulse_common.messages import sentiment_report as report_msg


class DatasetRepo(abc.ABC):
    """Interface for retrieving dataset analysis results."""

    @abc.abstractmethod
    def get_analysis_results(
        self,
        datasets: typing.List[report_msg.SentimentReportDataset],
        start_date: typing.Optional[str] = None,
        end_date: typing.Optional[str] = None,
        channel_title: typing.Optional[str] = None,
        excluded_channels: typing.List[str] = None,
    ) -> report_msg.AnalysisResults:
        """Retrieves analysis results for the provided datasets.

        Args:
          datasets: List of datasets to retrieve results for.
          start_date: Optional start date filter (ISO format).
          end_date: Optional end date filter (ISO format).
          channel_title: Optional channel title filter.
          excluded_channels: Optional list of channels to exclude.

        Returns:
          AnalysisResults populated with data from the datasets.
        """

    @abc.abstractmethod
    def get_channels(
        self,
        datasets: typing.List[report_msg.SentimentReportDataset],
        query: typing.Optional[str] = None,
    ) -> typing.List[str]:
        """Retrieves a list of unique channels for the provided datasets.

        Args:
          datasets: List of datasets to retrieve channels for.
          query: Optional query to filter channels by.

        Returns:
          List of unique channel names.
        """
        raise NotImplementedError
