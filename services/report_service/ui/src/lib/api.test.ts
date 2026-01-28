import {createReport, getReports} from './api';
import {
  SentimentReport,
  SocialMediaSource,
  SentimentDataType,
  ReportArtifactType,
} from './types';

// Mock global fetch
global.fetch = jest.fn();

describe('api.ts', () => {
  beforeEach(() => {
    jest.resetAllMocks();
    process.env.NEXT_PUBLIC_REPORTING_API_URL = 'http://localhost:8000';
  });

  describe('getReports', () => {
    it('should fetch reports successfully', async () => {
      const mockReports: SentimentReport[] = [
        {
          reportId: '123',
          topic: 'Test Topic',
          sources: [SocialMediaSource.REDDIT_POST],
          dataOutput: SentimentDataType.SENTIMENT_SCORE,
          datasets: [],
          reportArtifactType: ReportArtifactType.BQ_TABLE,
        },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockReports,
      });

      const result = await getReports();

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/reports',
        {
          cache: 'no-store',
        },
      );
      expect(result).toEqual(mockReports);
    });

    it('should throw error when fetch fails', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
      });

      await expect(getReports()).rejects.toThrow('Failed to fetch reports');
    });
  });

  describe('createReport', () => {
    it('should create a report successfully', async () => {
      const mockReport: SentimentReport = {
        reportId: '456',
        topic: 'New Topic',
        sources: [SocialMediaSource.YOUTUBE_VIDEO],
        dataOutput: SentimentDataType.SENTIMENT_SCORE,
        datasets: [],
        reportArtifactType: ReportArtifactType.BQ_TABLE,
      };
      const reportData = {
        topic: 'New Topic',
        sources: [SocialMediaSource.YOUTUBE_VIDEO],
        dataOutput: SentimentDataType.SENTIMENT_SCORE,
        reportArtifactType: ReportArtifactType.BQ_TABLE,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockReport,
      });

      const result = await createReport(reportData);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/report',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(reportData),
        },
      );
      expect(result).toEqual(mockReport);
    });

    it('should throw error when createReport fetch fails', async () => {
      const reportData = {
        topic: 'New Topic',
        sources: [SocialMediaSource.YOUTUBE_VIDEO],
        dataOutput: SentimentDataType.SENTIMENT_SCORE,
        reportArtifactType: ReportArtifactType.BQ_TABLE,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      await expect(createReport(reportData)).rejects.toThrow(
        'Failed to create report',
      );
    });
  });
});
