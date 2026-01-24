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

import {render, screen} from '@testing-library/react';
import CreateReportPage from './page';

jest.mock('@/components/create-report-form', () => ({
  CreateReportForm: jest.fn(() => <div>CreateReportForm</div>),
}));

describe('CreateReportPage', () => {
  it('should render the heading and the CreateReportForm component', () => {
    /**
     * Tests that the heading and the CreateReportForm component are rendered.
     *
     * Given the CreateReportPage component,
     * When it is rendered,
     * Then the main heading "Create a New Analysis" and the
     * CreateReportForm component should be visible.
     */
    render(<CreateReportPage />);

    expect(
      screen.getByRole('heading', {name: /Create a New Analysis/i}),
    ).toBeInTheDocument();
    expect(screen.getByText('CreateReportForm')).toBeInTheDocument();
  });
});
