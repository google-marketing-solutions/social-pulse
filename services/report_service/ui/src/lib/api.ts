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

import {SentimentReport as Report} from '@/lib/types';

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
 * @return A promise that resolves to the report.
 */
export async function getReportById(id: string): Promise<Report> {
  const baseUrl = process.env.REPORTING_API_URL;
  const response = await fetch(`${baseUrl}/api/report/${id}`, {
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
