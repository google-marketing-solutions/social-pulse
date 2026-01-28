import {
  getReports,
  createReport
} from './actions';
import {
  getReports as apiGetReports,
  createReport as apiCreateReport
} from './api';
import {
  SentimentReport,
  SocialMediaSource,
  SentimentDataType,
  ReportArtifactType,
} from './types';

// Mock the API module
jest.mock('./api', () => ({
  createReport: jest.fn(),
  getReports: jest.fn(),
}));

// Mock next/cache
jest.mock('next/cache', () => ({
  revalidatePath: jest.fn(),
}));

describe('actions.ts', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  describe('getReports', () => {
    it('should call api.getReports and return the result', async () => {
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

      (apiGetReports as jest.Mock).mockResolvedValue(mockReports);

      const result = await getReports();

      expect(apiGetReports).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockReports);
    });

    it('should propagate errors from api.getReports', async () => {
      const error = new Error('API Error');
      (apiGetReports as jest.Mock).mockRejectedValue(error);

      await expect(getReports()).rejects.toThrow(error);
    });
  });

  describe('createReport', () => {
    it('should call api.createReport with the provided arguments', async () => {
      const mockReport: SentimentReport = {
        reportId: '456',
        topic: 'New Topic',
        sources: [SocialMediaSource.YOUTUBE_VIDEO],
        dataOutput: SentimentDataType.SENTIMENT_SCORE,
        datasets: [],
        reportArtifactType: ReportArtifactType.BQ_TABLE,
      };
      (apiCreateReport as jest.Mock).mockResolvedValue(mockReport);

      const args = {
        topic: 'New Topic',
        sources: [SocialMediaSource.YOUTUBE_VIDEO],
        dataOutput: SentimentDataType.SENTIMENT_SCORE,
        reportArtifactType: ReportArtifactType.BQ_TABLE,
        dateRange: {
          from: new Date(),
          to: new Date(),
        },
      };
      const initialState = {
        message: '',
        success: false,
      };
      const result = await createReport(initialState, args);

      const expectedPayload = {
        topic: args.topic,
        sources: args.sources,
        dataOutput: args.dataOutput,
        startTime: args.dateRange!.from.toISOString(),
        endTime: args.dateRange!.to!.toISOString(),
        includeJustifications: false,
        reportArtifactType: args.reportArtifactType,
        datasets: [],
      };

      expect(apiCreateReport).toHaveBeenCalledTimes(1);
      expect(apiCreateReport).toHaveBeenCalledWith(expectedPayload);
      expect(result).toEqual({
        success: true,
        message: 'Report created successfully.',
      });
    });

    it('should propagate errors from api.createReport', async () => {
      const error = new Error('Create API Error');
      (apiCreateReport as jest.Mock).mockRejectedValue(error);

      const args = {
        topic: 'Error Topic',
        sources: [SocialMediaSource.REDDIT_POST],
        dataOutput: SentimentDataType.SENTIMENT_SCORE,
        reportArtifactType: ReportArtifactType.BQ_TABLE,
        dateRange: {
          from: new Date(),
          to: new Date(),
        },
      };
      const initialState = {
        message: '',
        success: false,
      };
      const result = await createReport(initialState, args);
      expect(result).toEqual({
        success: false,
        message: 'Network error creating report.',
      });
    });
  });
});
