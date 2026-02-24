import {render, screen} from '@testing-library/react';
import {ReportJustificationCharts} from './report-justification-charts';
import {JustificationBreakdown} from '@/lib/types';

describe('ReportJustificationCharts', () => {
  const mockBreakdown: JustificationBreakdown = {
    positive: [
      {category: 'Great Service', count: 80},
      {category: 'Good Quality', count: 20},
    ],
    negative: [
      {category: 'Slow Shipping', count: 30},
      {category: 'Damaged Item', count: 10},
    ],
    neutral: [],
  };

  it('renders positive and negative justification lists', () => {
    render(<ReportJustificationCharts breakdown={mockBreakdown} />);

    expect(screen.getByText('Positive Justifications')).toBeInTheDocument();
    expect(screen.getByText('Negative Justifications')).toBeInTheDocument();

    // Check for categories
    expect(screen.getByText('Great Service')).toBeInTheDocument();
    expect(screen.getByText('Good Quality')).toBeInTheDocument();
    expect(screen.getByText('Slow Shipping')).toBeInTheDocument();
    expect(screen.getByText('Damaged Item')).toBeInTheDocument();

    // Check for counts (using regex for partial match if needed, or exact)
    expect(screen.getByText('80')).toBeInTheDocument();
    expect(screen.getByText('20')).toBeInTheDocument();
    expect(screen.getByText('30')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();

    // Check for percentages
    // Positive total = 100. 80 -> 80.0%, 20 -> 20.0%
    expect(screen.getByText('(80.0%)')).toBeInTheDocument();
    expect(screen.getByText('(20.0%)')).toBeInTheDocument();

    // Negative total = 40. 30 -> 75.0%, 10 -> 25.0%
    expect(screen.getByText('(75.0%)')).toBeInTheDocument();
    expect(screen.getByText('(25.0%)')).toBeInTheDocument();
  });

  it('renders nothing when data is empty', () => {
    const emptyBreakdown: JustificationBreakdown = {
      positive: [],
      negative: [],
      neutral: [],
    };
    const {container} = render(
      <ReportJustificationCharts breakdown={emptyBreakdown} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('handles single justification type gracefully', () => {
    const partialBreakdown: JustificationBreakdown = {
      positive: [{category: 'Only Positive', count: 10}],
      negative: [],
      neutral: [],
    };
    render(<ReportJustificationCharts breakdown={partialBreakdown} />);

    expect(screen.getByText('Positive Justifications')).toBeInTheDocument();
    // Negative section might still be rendered but empty or "No data available" depending on implementation
    // Current implementation renders "No data available" inside the card if data is empty but list component is called.
    // Wait, ReportJustificationCharts calls JustificationList for both.
    // JustificationList checks !data?.length and returns "No data available" card.

    expect(screen.getByText('Negative Justifications')).toBeInTheDocument();
    expect(screen.getAllByText('No data available')).toHaveLength(1); // One for negative
  });
});
