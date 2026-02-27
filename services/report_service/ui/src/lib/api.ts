// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import {SentimentReport as Report, ReportInsight} from '@/lib/types';

/**
 * Creates a new sentiment report by making a POST request to the backend API.
 *
 * @param report The report data to be sent to the backend.
 * @return A promise that resolves to the created report data from the backend.
 */
export async function createReport(report: Report): Promise<Report> {
  const baseUrl = process.env.REPORTING_API_URL;
  console.log('Creating report with payload: ', JSON.stringify(report));

  const response = await fetch(`${baseUrl}/api/report`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(report),
  });

  if (!response.ok) {
    throw new Error('Failed to create report');
  }

  const data = await response.json();
  return data;
}

/**
 * Fetches all sentiment reports.
 *
 * @return A promise that resolves to a list of reports.
 */
export async function getReports(): Promise<Report[]> {
  const baseUrl = process.env.REPORTING_API_URL;
  const response = await fetch(`${baseUrl}/api/reports`, {
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error('Failed to fetch reports');
  }

  const data = await response.json();
  return data;
}

/**
 * Fetches a single report by ID.
 *
 * @param id The ID of the report to fetch.
 * @param filters Optional filters to apply to the report analysis results.
 * @return A promise that resolves to the report.
 */
export async function getReportById(
  id: string,
  filters?: {
    channelTitle?: string;
    startDate?: string;
    endDate?: string;
    excludedChannels?: string[];
  },
): Promise<Report> {
  const baseUrl = process.env.REPORTING_API_URL;
  const url = new URL(`${baseUrl}/api/report/${id}`);

  if (filters?.channelTitle) {
    url.searchParams.append('channel_title', filters.channelTitle);
  }
  if (filters?.startDate) {
    url.searchParams.append('start_date', filters.startDate);
  }
  if (filters?.endDate) {
    url.searchParams.append('end_date', filters.endDate);
  }
  if (filters?.excludedChannels?.length) {
    filters.excludedChannels.forEach(channel =>
      url.searchParams.append('excluded_channels', channel),
    );
  }

  const response = await fetch(url.toString(), {
    cache: 'no-store',
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Report not found');
    }
    throw new Error('Failed to fetch report');
  }

  const data = await response.json();
  return data;
}

/**
 * Fetches the list of channels available for a report.
 * @param id The ID of the report.
 * @return A list of channel names.
 */
export async function getReportChannels(
  id: string,
  query?: string,
): Promise<string[]> {
  const baseUrl = process.env.REPORTING_API_URL;
  const url = new URL(`${baseUrl}/api/report/${id}/channels`);

  if (query) {
    url.searchParams.append('query', query);
  }

  const response = await fetch(url.toString(), {
    cache: 'no-store',
  });

  if (!response.ok) {
    console.error(
      `Failed to fetch channels for report ${id}:`,
      response.statusText,
    );
    return [];
  }

  return response.json();
}

/**
 * Fetches insights for a single report by ID.
 *
 * @param id The ID of the report to fetch insights for.
 * @return A promise that resolves to a list of insights.
 */
// TODO(jcryan): Add API tests for this function.
export async function getInsightsById(id: string): Promise<ReportInsight[]> {
  const baseUrl = process.env.REPORTING_API_URL;
  const url = new URL(`${baseUrl}/api/insights/${id}`);

  const response = await fetch(url.toString(), {
    cache: 'no-store',
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Insights not found');
    }
    throw new Error('Failed to fetch insights');
  }

  const data = await response.json();
  return data;
}
