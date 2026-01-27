// Copyright 2024 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import {render, screen, fireEvent, waitFor} from '@testing-library/react';
import {CreateReportForm} from './create-report-form';
import {createReport} from '@/lib/actions';
import {useToast} from '@/hooks/use-toast';
import {useRouter} from 'next/navigation';

jest.mock('@/lib/actions', () => ({
  createReport: jest.fn(),
}));

jest.mock('@/hooks/use-toast', () => ({
  useToast: jest.fn(() => ({
    toast: jest.fn(),
  })),
}));

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
  })),
}));

const mockedCreateReport = createReport as jest.Mock;
const mockedUseToast = useToast as jest.Mock;
const mockedUseRouter = useRouter as jest.Mock;

describe('CreateReportForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Set up default mock implementations
    mockedUseToast.mockReturnValue({toast: jest.fn()});
    mockedUseRouter.mockReturnValue({push: jest.fn()});
  });

  it('should render the form with default values', () => {
    /**
     * Tests that the form renders with default values.
     *
     * Given the CreateReportForm component,
     * When it is rendered,
     * Then the form fields for topic, sources, and analysis type are visible.
     */
    render(<CreateReportForm />);
    expect(screen.getByLabelText(/Topic/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Sentiment Analysis/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Share of Voice/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/YouTube Video/i)).toBeInTheDocument();
    expect(screen.getByText(/Create Report/i)).toBeInTheDocument();
  });

  it('should display validation errors for invalid submission', async () => {
    /**
     * Tests that validation errors are displayed for invalid submission.
     *
     * Given the CreateReportForm component,
     * When the form is submitted with an empty topic,
     * Then a validation error message for the topic field is displayed.
     */
    render(<CreateReportForm />);
    fireEvent.change(screen.getByLabelText(/Topic/i), {
      target: {value: ''},
    });
    fireEvent.click(screen.getByText(/Create Report/i));

    await waitFor(() => {
      expect(
        screen.getByText(/Topic must be at least 3 characters/i),
      ).toBeInTheDocument();
    });
  });

  it('should show a toast and redirect on successful submission', async () => {
    /**
     * Tests that a toast is shown and the user is redirected on successful
     * submission.
     *
     * Given the CreateReportForm component,
     * When valid data is entered and the form is submitted successfully,
     * Then a success toast is displayed and the user is redirected to the home
     * page.
     */
    const toast = jest.fn();
    const push = jest.fn();
    mockedUseToast.mockReturnValue({toast});
    mockedUseRouter.mockReturnValue({push});
    mockedCreateReport.mockResolvedValue({
      success: true,
      message: 'Success!',
    });

    render(<CreateReportForm />);
    fireEvent.change(screen.getByLabelText(/Topic/i), {
      target: {value: 'Valid Topic'},
    });
    fireEvent.click(screen.getByText(/Create Report/i));

    await waitFor(() => {
      expect(mockedCreateReport).toHaveBeenCalled();
      expect(toast).toHaveBeenCalledWith({
        title: 'Report submitted!',
        description: 'Your new analysis is being generated.',
      });
      expect(push).toHaveBeenCalledWith('/');
    });
  });

  it('should show an error toast on failed submission', async () => {
    /**
     * Tests that an error toast is shown on failed submission.
     *
     * Given the CreateReportForm component,
     * When the form is submitted and the API call fails,
     * Then an error toast is displayed with the error message from the API.
     */
    const toast = jest.fn();
    mockedUseToast.mockReturnValue({toast});
    const errorMessage = 'Network Error';
    mockedCreateReport.mockResolvedValue({
      success: false,
      message: errorMessage,
    });

    render(<CreateReportForm />);
    fireEvent.change(screen.getByLabelText(/Topic/i), {
      target: {value: 'Valid Topic'},
    });
    fireEvent.click(screen.getByText(/Create Report/i));

    await waitFor(() => {
      expect(mockedCreateReport).toHaveBeenCalled();
      expect(toast).toHaveBeenCalledWith({
        variant: 'destructive',
        title: 'Error submitting form',
        description: errorMessage,
      });
    });
  });

  it('should disable the submit button during submission', async () => {
    /**
     * Tests that the submit button is disabled during submission.
     *
     * Given the CreateReportForm component,
     * When the form is submitted,
     * Then the submit button is disabled and its text changes to "Creating...".
     */
    mockedCreateReport.mockImplementation(
      () =>
        new Promise(resolve => setTimeout(() => resolve({success: true}), 100)),
    );

    render(<CreateReportForm />);
    fireEvent.change(screen.getByLabelText(/Topic/i), {
      target: {value: 'A valid topic'},
    });
    fireEvent.click(screen.getByRole('button', {name: /Create Report/i}));

    await waitFor(() => {
      const button = screen.getByRole('button', {name: /Creating.../i});
      expect(button).toBeDisabled();
    });
  });
});
