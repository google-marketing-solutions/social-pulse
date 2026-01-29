import {createReport, getReports, getReportById} from './api';
import {
  SentimentReport,
  SentimentDataType,
  SocialMediaSource,
  Status,
  ReportArtifactType,
} from './types';
import fetchMock from 'jest-fetch-mock';

fetchMock.enableMocks();

describe('API Service', () => {
  const mockBaseUrl = 'http://localhost:8000';

  beforeEach(() => {
    fetchMock.resetMocks();
    process.env.NEXT_PUBLIC_REPORTING_API_URL = mockBaseUrl;
  });

  const mockReport: SentimentReport = {
    reportId: '123',
    topic: 'Test Topic',
    status: Status.PENDING,
    sources: [SocialMediaSource.X_POST],
    dataOutput: SentimentDataType.SENTIMENT_SCORE,
    reportArtifactType: ReportArtifactType.BQ_TABLE,
    datasets: [],
  };

  describe('createReport', () => {
    it('should create a report successfully', async () => {
      fetchMock.mockResponseOnce(JSON.stringify(mockReport));

      const result = await createReport(mockReport);

      expect(fetchMock).toHaveBeenCalledWith(`${mockBaseUrl}/api/report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(mockReport),
      });
      expect(result).toEqual(mockReport);
    });

    it('should throw an error when creation fails', async () => {
      fetchMock.mockResponseOnce(JSON.stringify({}), {status: 500});

      await expect(createReport(mockReport)).rejects.toThrow(
        'Failed to create report',
      );
    });
  });

  describe('getReports', () => {
    it('should fetch reports successfully', async () => {
      const mockReports = [mockReport];
      fetchMock.mockResponseOnce(JSON.stringify(mockReports));

      const result = await getReports();

      expect(fetchMock).toHaveBeenCalledWith(`${mockBaseUrl}/api/reports`, {
        cache: 'no-store',
      });
      expect(result).toEqual(mockReports);
    });

    it('should throw an error when fetching reports fails', async () => {
      fetchMock.mockResponseOnce(JSON.stringify({}), {status: 500});

      await expect(getReports()).rejects.toThrow('Failed to fetch reports');
    });
  });

  describe('getReportById', () => {
    it('should fetch a single report successfully', async () => {
      fetchMock.mockResponseOnce(JSON.stringify(mockReport));

      const result = await getReportById('123');

      expect(fetchMock).toHaveBeenCalledWith(`${mockBaseUrl}/api/report/123`, {
        cache: 'no-store',
      });
      expect(result).toEqual(mockReport);
    });

    it('should throw "Report not found" for 404', async () => {
      fetchMock.mockResponseOnce(JSON.stringify({}), {status: 404});

      await expect(getReportById('123')).rejects.toThrow('Report not found');
    });

    it('should throw generic error for other failures', async () => {
      fetchMock.mockResponseOnce(JSON.stringify({}), {status: 500});

      await expect(getReportById('123')).rejects.toThrow(
        'Failed to fetch report',
      );
    });
  });
});
