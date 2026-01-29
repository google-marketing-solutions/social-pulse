import {createReport, getReports, getReportById} from './actions';
import * as api from './api';
import {revalidatePath} from 'next/cache';
import {SentimentDataType, SocialMediaSource, Status} from './types';
import fs from 'fs/promises';

// Mock dependencies
jest.mock('./api');
jest.mock('next/cache');
jest.mock('fs/promises');

describe('Server Actions', () => {
  const mockReport = {
    reportId: '123',
    topic: 'Test Topic',
    status: Status.PENDING,
    sources: [SocialMediaSource.X_POST],
    dataOutput: SentimentDataType.SENTIMENT_SCORE,
    datasets: [],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (fs.readFile as jest.Mock).mockResolvedValue('[]');
    (fs.writeFile as jest.Mock).mockResolvedValue(undefined);
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
