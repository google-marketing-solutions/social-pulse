import {render, screen, fireEvent} from '@testing-library/react';
import {ReportsList} from './reports-list';
import {
  ReportForList,
  Status,
  SocialMediaSource,
  SentimentDataType,
  ReportArtifactType,
} from '@/lib/types';
import {useRouter} from 'next/navigation';

// Mock useRouter
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

describe('ReportsList', () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.resetAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });
  });

  const mockReports: ReportForList[] = [
    {
      reportId: '1',
      topic: 'React Testing',
      status: Status.COMPLETED,
      sources: [SocialMediaSource.REDDIT_POST],
      dataOutput: SentimentDataType.SENTIMENT_SCORE,
      startTime: '2024-01-01T00:00:00Z',
      endTime: '2024-01-07T00:00:00Z',
      createdOn: '2024-01-08T00:00:00Z',
      reportArtifactType: ReportArtifactType.BQ_TABLE,
    },
    {
      reportId: '2',
      topic: 'Angular Testing',
      status: Status.FAILED,
      sources: [SocialMediaSource.X_POST],
      dataOutput: SentimentDataType.SENTIMENT_SCORE,
      startTime: '2024-02-01T00:00:00Z',
      endTime: '2024-02-07T00:00:00Z',
      createdOn: '2024-02-08T00:00:00Z',
      reportArtifactType: ReportArtifactType.BQ_TABLE,
    },
  ];

  it('renders "No reports found" when reports array is empty', () => {
    render(<ReportsList reports={[]} />);
    expect(screen.getByText('No reports found')).toBeInTheDocument();
  });

  it('renders list of reports correctly', () => {
    render(<ReportsList reports={mockReports} />);

    // Check topics
    expect(screen.getByText('React Testing')).toBeInTheDocument();
    expect(screen.getByText('Angular Testing')).toBeInTheDocument();

    // Check Statuses
    expect(screen.getByText('COMPLETED')).toBeInTheDocument();
    expect(screen.getByText('FAILED')).toBeInTheDocument();
  });

  it('navigates to report details when clicking a completed report', () => {
    render(<ReportsList reports={mockReports} />);

    // Click the row for report 1
    fireEvent.click(screen.getByText('React Testing').closest('tr')!);

    expect(mockPush).toHaveBeenCalledWith('/reports/1');
  });

  it('does NOT navigate when clicking a failed report (if logic prevents it)', () => {
    // Note: The original component has onClick for FAILED reports too?
    // Let's check the code:
    // if (status === 'COMPLETED' || ... || 'GENERATING_REPORT')
    // It DOES NOT include FAILED in the if condition.

    render(<ReportsList reports={mockReports} />);

    fireEvent.click(screen.getByText('Angular Testing').closest('tr')!);

    expect(mockPush).not.toHaveBeenCalled();
  });

  it('navigates for NEW reports', () => {
    const newReport: ReportForList = {
      ...mockReports[0],
      reportId: '3',
      status: Status.NEW,
      topic: 'New Report',
    };

    render(<ReportsList reports={[newReport]} />);
    fireEvent.click(screen.getByText('New Report').closest('tr')!);
    expect(mockPush).toHaveBeenCalledWith('/reports/3');
  });
});
