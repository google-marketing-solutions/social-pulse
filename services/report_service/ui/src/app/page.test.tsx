import {render} from '@testing-library/react';
import ReportsListPage from './page';
import {getReports} from '@/lib/actions';
import {
  Status,
  ReportArtifactType,
  SentimentReport,
  SentimentDataType,
} from '@/lib/types';
import {ReportsList} from '@/components/reports-list';

// Mock the actions
jest.mock('@/lib/actions', () => ({
  getReports: jest.fn(),
}));

// Mock the ReportsList component
jest.mock('@/components/reports-list', () => ({
  ReportsList: jest.fn(() => <div>Mocked Reports List</div>),
}));

describe('ReportsListPage', () => {
  const mockReports: SentimentReport[] = [
    {
      reportId: '1',
      topic: 'Test Logic',
      status: Status.COMPLETED,
      datasets: [],
      sources: [],
      dataOutput: SentimentDataType.SENTIMENT_SCORE,
      reportArtifactType: ReportArtifactType.BQ_TABLE,
    },
  ];

  beforeEach(() => {
    jest.resetAllMocks();
  });

  it('fetches reports and renders ReportsList', async () => {
    (getReports as jest.Mock).mockResolvedValue(mockReports);

    const Page = await ReportsListPage();
    render(Page);

    expect(getReports).toHaveBeenCalledTimes(1);
    expect(ReportsList).toHaveBeenCalledWith(
      expect.objectContaining({
        reports: expect.arrayContaining([
          expect.objectContaining({
            reportId: '1',
            topic: 'Test Logic',
          }),
        ]),
      }),
      {},
    );

    // Verify datasets was stripped (ReportForList type check logic)
    // The mock receives the object, we can verify it doesn't have datasets if we want strictness,
    // but the component logic in page.tsx does `const {datasets, ...rest} = report;`.
    // Let's verify ReportsList was called with the stripped object.
    const calledProps = (ReportsList as jest.Mock).mock.calls[0][0];
    expect(calledProps.reports[0].datasets).toBeUndefined();
  });
});
