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
import '@testing-library/jest-dom';
import {render, screen, fireEvent, waitFor} from '@testing-library/react';
import {ReportFilters} from './report-filters';
import {useRouter, usePathname, useSearchParams} from 'next/navigation';
import {getReportChannels} from '@/lib/actions';

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
  useSearchParams: jest.fn(),
}));

jest.mock('@/lib/actions', () => ({
  getReportChannels: jest.fn(),
}));

describe('ReportFilters', () => {
  const mockRouter = {push: jest.fn(), replace: jest.fn()};
  const mockSearchParams = new URLSearchParams();

  beforeEach(() => {
    // Mock ResizeObserver
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };

    window.HTMLElement.prototype.scrollIntoView = jest.fn();
    window.HTMLElement.prototype.releasePointerCapture = jest.fn();
    window.HTMLElement.prototype.hasPointerCapture = jest.fn();

    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (usePathname as jest.Mock).mockReturnValue('/reports/123');
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);
    (getReportChannels as jest.Mock).mockResolvedValue([]);
  });

  it('renders report filters', () => {
    render(<ReportFilters reportId="123" />);
    // Initial text should indicate selection or search
    expect(screen.getByText(/Select channels to exclude/i)).toBeInTheDocument();
    expect(screen.getByText('Start Date')).toBeInTheDocument();
  });

  it('fetches channels when searching', async () => {
    (getReportChannels as jest.Mock).mockResolvedValue([
      'Channel A',
      'Channel B',
    ]);
    render(<ReportFilters reportId="123" />);

    // Open dialog
    fireEvent.click(screen.getByText(/Select channels to exclude/i));

    // Type in search
    const searchInput = screen.getByPlaceholderText('Search channel...');
    fireEvent.change(searchInput, {target: {value: 'Channel'}});

    await waitFor(() => {
      expect(getReportChannels).toHaveBeenCalledWith('123', 'Channel');
    });

    expect(screen.getByText('Channel A')).toBeInTheDocument();
  });
});
