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
import {render, screen} from '@testing-library/react';
import ReportDetailPage from './page';
import {getReportById} from '@/lib/actions';
import {
  SentimentReport,
  SocialMediaSource,
  Status,
  SentimentDataType,
  ReportArtifactType,
} from '@/lib/types';
import {notFound} from 'next/navigation';

// Mock dependencies
jest.mock('@/lib/actions', () => ({
  getReportById: jest.fn(),
}));

jest.mock('next/navigation', () => ({
  notFound: jest.fn(() => {
    throw new Error('NEXT_NOT_FOUND');
  }),
}));

jest.mock('@/components/report-sentiment-charts', () => ({
  ReportSentimentCharts: () => (
    <div data-testid="sentiment-charts">Sentiment Charts</div>
  ),
}));

jest.mock('@/components/report-share-of-voice-charts', () => ({
  ReportShareOfVoiceCharts: () => (
    <div data-testid="sov-charts">Share of Voice Charts</div>
  ),
}));

jest.mock('@/components/report-filters', () => ({
  ReportFilters: ({reportId}: {reportId: string}) => (
    <div data-testid="report-filters" data-report-id={reportId}>
      Report Filters
    </div>
  ),
}));

describe('ReportDetailPage', () => {
  const mockParams = Promise.resolve({id: '123'});
  const mockSearchParams = Promise.resolve({});

  const mockReport: SentimentReport = {
    reportId: '123',
    topic: 'Test Topic',
    status: Status.COMPLETED,
    sources: [SocialMediaSource.YOUTUBE_VIDEO],
    dataOutput: SentimentDataType.SENTIMENT_SCORE,
    analysisResults: {
      [SocialMediaSource.YOUTUBE_VIDEO]: {
        sentimentOverTime: [],
        overallSentiment: {positive: 0, negative: 0, neutral: 0, average: 0},
      },
    },
    reportArtifactType: ReportArtifactType.BQ_TABLE,
    datasets: [],
    startTime: '2023-01-01T00:00:00Z',
    endTime: '2023-01-31T23:59:59Z',
    createdOn: '2023-01-01T00:00:00Z',
  };

  beforeEach(() => {
    jest.resetAllMocks();
  });

  it('calls notFound when report is missing', async () => {
    (getReportById as jest.Mock).mockResolvedValue(undefined);

    await ReportDetailPage({
      params: mockParams,
      searchParams: mockSearchParams,
    });

    expect(notFound).toHaveBeenCalled();
  });

  it('renders pending state when status is not completed/failed', async () => {
    (getReportById as jest.Mock).mockImplementation(() =>
      Promise.resolve({
        ...mockReport,
        status: Status.GENERATING_REPORT,
      }),
    );

    const jsx = await ReportDetailPage({
      params: mockParams,
      searchParams: mockSearchParams,
    });
    render(jsx);

    expect(
      screen.getByText(/Analysis is GENERATING REPORT/i),
    ).toBeInTheDocument();
    expect(screen.queryByTestId('sentiment-charts')).not.toBeInTheDocument();
  });

  it('renders sentiment charts when completed and dataOutput is SENTIMENT_SCORE', async () => {
    (getReportById as jest.Mock).mockImplementation(() =>
      Promise.resolve({
        ...mockReport,
        dataOutput: SentimentDataType.SENTIMENT_SCORE,
      }),
    );

    const jsx = await ReportDetailPage({
      params: mockParams,
      searchParams: mockSearchParams,
    });
    render(jsx);

    expect(screen.getByTestId('sentiment-charts')).toBeInTheDocument();
    expect(screen.queryByTestId('sov-charts')).not.toBeInTheDocument();
  });

  it('renders share of voice charts when completed and dataOutput is SHARE_OF_VOICE', async () => {
    (getReportById as jest.Mock).mockImplementation(() =>
      Promise.resolve({
        ...mockReport,
        dataOutput: 'SHARE_OF_VOICE',
      }),
    );

    const jsx = await ReportDetailPage({
      params: mockParams,
      searchParams: mockSearchParams,
    });
    render(jsx);

    expect(screen.getByTestId('sov-charts')).toBeInTheDocument();
    expect(screen.queryByTestId('sentiment-charts')).not.toBeInTheDocument();
  });

  it('renders correct data in cards', async () => {
    (getReportById as jest.Mock).mockResolvedValue(mockReport);

    const jsx = await ReportDetailPage({
      params: mockParams,
      searchParams: mockSearchParams,
    });
    render(jsx);

    expect(screen.getByText('Test Topic')).toBeInTheDocument();
    expect(screen.getByText(/sentiment score/i)).toBeInTheDocument(); // data output
    expect(screen.getAllByText(/YouTube Videos/i).length).toBeGreaterThan(0); // source appears multiple times
  });

  it('passes reportId to ReportFilters', async () => {
    (getReportById as jest.Mock).mockResolvedValue(mockReport);

    const jsx = await ReportDetailPage({
      params: mockParams,
      searchParams: mockSearchParams,
    });
    render(jsx);

    const filters = screen.getByTestId('report-filters');
    expect(filters).toHaveAttribute('data-report-id', '123');
  });
});
