// Copyright 2024 Google LLC
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

import {createReport} from './actions';
import {createReport as apiCreateReport} from './api';
import {SocialMediaSource, SentimentDataType} from './types';
import {revalidatePath} from 'next/cache';
import fs from 'fs/promises';

jest.mock('./api', () => ({
  createReport: jest.fn(),
}));

jest.mock('fs/promises', () => ({
  readFile: jest.fn(),
  writeFile: jest.fn(),
}));

jest.mock('next/cache', () => ({
  revalidatePath: jest.fn(),
}));

const mockedApiCreateReport = apiCreateReport as jest.Mock;
const mockedFsReadFile = fs.readFile as jest.Mock;
const mockedFsWriteFile = fs.writeFile as jest.Mock;
const mockedRevalidatePath = revalidatePath as jest.Mock;

describe('createReport action', () => {
  const prevState = {};

  beforeEach(() => {
    jest.resetAllMocks();
  });

  it('should return a validation error for invalid data', async () => {
    /**
     * Tests that a validation error is returned for invalid data.
     *
     * Given invalid form data (e.g., an empty topic),
     * When the createReport action is invoked,
     * Then it returns a state object with a validation error message
     * and `success: false`.
     */
    const invalidData = {
      topic: '', // Invalid topic
      sources: [SocialMediaSource.YOUTUBE_VIDEO],
      dataOutput: SentimentDataType.SENTIMENT_SCORE,
      dateRange: {
        from: new Date(),
        to: new Date(),
      },
    };

    const result = await createReport(prevState, invalidData);

    expect(result.success).toBe(false);
    expect(result.errors?.topic).toBeDefined();
    expect(result.message).toContain('check the fields');
    expect(apiCreateReport).not.toHaveBeenCalled();
  });

  it('should call the API and return success for valid data', async () => {
    /**
     * Tests that the API is called and returns success for valid data.
     *
     * Given valid form data,
     * When the createReport action is invoked,
     * Then the `apiCreateReport` function is called with the correct payload,
     * the cache is revalidated, and the function returns a success state.
     */
    const validData = {
      topic: 'Test Topic',
      sources: [SocialMediaSource.YOUTUBE_VIDEO],
      dataOutput: SentimentDataType.SENTIMENT_SCORE,
      dateRange: {
        from: new Date('2024-01-01'),
        to: new Date('2024-01-31'),
      },
    };
    const newReport = {id: '123', ...validData};

    mockedApiCreateReport.mockResolvedValue(newReport);
    mockedFsReadFile.mockResolvedValue(JSON.stringify([]));

    const result = await createReport(prevState, validData);

    expect(result.success).toBe(true);
    expect(result.message).toBe('Report created successfully.');
    expect(mockedApiCreateReport).toHaveBeenCalledTimes(1);
    expect(mockedFsReadFile).toHaveBeenCalled();
    expect(mockedFsWriteFile).toHaveBeenCalled();
    expect(mockedRevalidatePath).toHaveBeenCalledWith('/');
    expect(mockedRevalidatePath).toHaveBeenCalledWith('/create');
  });

  it('should return an error message if the API call fails', async () => {
    /**
     * Tests that an error message is returned if the API call fails.
     *
     * Given valid form data,
     * When the createReport action is invoked and the API call fails,
     * Then a state object with a network error message and `success: false`
     * is returned.
     */
    const consoleErrorSpy = jest
      .spyOn(console, 'error')
      .mockImplementation(() => {});

    const validData = {
      topic: 'Test Topic',
      sources: [SocialMediaSource.YOUTUBE_VIDEO],
      dataOutput: SentimentDataType.SENTIMENT_SCORE,
      dateRange: {
        from: new Date('2024-01-01'),
        to: new Date('2024-01-31'),
      },
    };

    mockedApiCreateReport.mockRejectedValue(new Error('API Error'));

    const result = await createReport(prevState, validData);

    expect(result.success).toBe(false);
    expect(result.message).toBe('Network error creating report.');
    expect(apiCreateReport).toHaveBeenCalledTimes(1);
    consoleErrorSpy.mockRestore();
  });
});
