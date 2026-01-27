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
  const baseUrl = process.env.NEXT_PUBLIC_REPORTING_API_URL;
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

  return response.json();
}
