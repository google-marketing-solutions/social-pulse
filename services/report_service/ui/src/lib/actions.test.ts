//  Copyright 2025 Google LLC
//
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at
//
//      https://www.apache.org/licenses/LICENSE-2.0
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.

import {createReport, getReports, getReportById} from './actions';
import * as api from './api';
import {revalidatePath} from 'next/cache';
import {SentimentDataType, SocialMediaSource, Status} from './types';


// Mock dependencies
jest.mock('./api');
jest.mock('next/cache');


describe('Server Actions', () => {
  const mockReport = {
    reportId: '123',
    topic: 'Test Topic',
    status: Status.NEW,
    sources: [SocialMediaSource.X_POST],
    dataOutput: SentimentDataType.SENTIMENT_SCORE,
    datasets: [],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('createReport', () => {
    const validFormData = {
      topic: 'Test Topic',
      sources: [SocialMediaSource.X_POST],
      dataOutput: SentimentDataType.SENTIMENT_SCORE,
      dateRange: {
        from: new Date('2023-01-01'),
        to: new Date('2023-01-31'),
      },
    };

    it('should create a report successfully', async () => {
      (api.createReport as jest.Mock).mockResolvedValue(mockReport);

      const result = await createReport({}, validFormData);

      expect(api.createReport).toHaveBeenCalled();
      expect(revalidatePath).toHaveBeenCalledWith('/');
      expect(revalidatePath).toHaveBeenCalledWith('/create');
      expect(result).toEqual({
        success: true,
        message: 'Report created successfully.',
      });
    });

    it('should return errors for invalid data', async () => {
      const invalidData = {
        topic: '', // Invalid empty topic
        sources: [],
        dataOutput: 'INVALID' as SentimentDataType,
      };

      const result = await createReport({}, invalidData);

      expect(result.success).toBe(false);
      expect(result.errors).toBeDefined();
      expect(api.createReport).not.toHaveBeenCalled();
    });

    it('should return error message on API failure', async () => {
      (api.createReport as jest.Mock).mockRejectedValue(new Error('API Error'));

      const result = await createReport({}, validFormData);

      expect(result.success).toBe(false);
      expect(result.message).toBe('Network error creating report.');
    });
  });

  describe('getReports', () => {
    it('should fetch reports from API', async () => {
      (api.getReports as jest.Mock).mockResolvedValue([mockReport]);

      const result = await getReports();

      expect(api.getReports).toHaveBeenCalled();
      expect(result).toEqual([mockReport]);
    });
  });

  describe('getReportById', () => {
    it('should fetch report by ID', async () => {
      (api.getReportById as jest.Mock).mockResolvedValue(mockReport);

      const result = await getReportById('123');

      expect(api.getReportById).toHaveBeenCalledWith('123');
      expect(result).toEqual(mockReport);
    });

    it('should return undefined on error', async () => {
      (api.getReportById as jest.Mock).mockRejectedValue(
        new Error('Not found'),
      );

      const result = await getReportById('123');

      expect(result).toBeUndefined();
    });
  });
});
