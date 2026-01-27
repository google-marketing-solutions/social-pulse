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

import {createReport} from '@/lib/api';
import {
  SentimentReport as Report,
  Status,
  SocialMediaSource,
  SentimentDataType,
  ReportArtifactType,
} from '@/lib/types';

// Mock the global fetch function
global.fetch = jest.fn();

const mockReport: Report = {
  reportId: '123',
  // reportName: 'Test Report', // This property doesn't exist on SentimentReport
  topic: 'Test Report',
  sources: [SocialMediaSource.YOUTUBE_VIDEO],
  dataOutput: SentimentDataType.SENTIMENT_SCORE,
  startTime: '2024-01-01T00:00:00Z',
  endTime: '2024-01-02T00:00:00Z',
  status: Status.NEW,
  reportArtifactType: ReportArtifactType.BQ_TABLE,
  reportArtifactUri: '',
  createdOn: '2024-01-01T00:00:00Z',
  datasets: [],
};

describe('createReport', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    process.env.NEXT_PUBLIC_REPORTING_API_URL = 'http://test-api';
  });

  it('should create a report successfully', async () => {
    /**
     * Tests successful report creation.
     *
     * Given valid report data,
     * When createReport is called,
     * Then a POST request is made to the correct API endpoint
     * and the function returns the created report data.
     */
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockReport,
    });

    const result = await createReport(mockReport);

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith('http://test-api/api/report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(mockReport),
    });
    expect(result).toEqual(mockReport);
  });

  it('should throw an error if the API call fails', async () => {
    /**
     * Tests report creation failure.
     *
     * Given valid report data,
     * When createReport is called and the API returns an error,
     * Then an error is thrown.
     */
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
    });

    await expect(createReport(mockReport)).rejects.toThrow(
      'Failed to create report',
    );

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith('http://test-api/api/report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(mockReport),
    });
  });
});
