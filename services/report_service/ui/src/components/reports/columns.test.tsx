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
import {columns} from './columns';
import {SocialMediaSource, Status, ReportForList} from '@/lib/types';
import {ColumnDef, Row} from '@tanstack/react-table';

describe('columns filter functions', () => {
  const getFilterFn = (columnId: string) => {
    const column = columns.find(
      c =>
        (c as ColumnDef<ReportForList> & {accessorKey?: string}).accessorKey ===
          columnId ||
        (c as ColumnDef<ReportForList> & {id?: string}).id === columnId,
    );
    return column?.filterFn;
  };

  it('filters sources correctly', () => {
    const filterFn = getFilterFn('sources');
    expect(filterFn).toBeDefined();

    const mockRow = {
      getValue: () => [
        SocialMediaSource.YOUTUBE_VIDEO,
        SocialMediaSource.REDDIT_POST,
      ],
    } as unknown as Row<ReportForList>;

    // Filter selects YOUTUBE_VIDEO -> Should match
    expect(
      filterFn!(mockRow, 'sources', [SocialMediaSource.YOUTUBE_VIDEO]),
    ).toBe(true);

    // Filter selects X_POST -> Should NOT match
    expect(filterFn!(mockRow, 'sources', [SocialMediaSource.X_POST])).toBe(
      false,
    );

    // Filter selects REDDIT_POST -> Should match
    expect(filterFn!(mockRow, 'sources', [SocialMediaSource.REDDIT_POST])).toBe(
      true,
    );

    // Filter selects YOUTUBE_VIDEO and X_POST -> Should match (OR logic)
    expect(
      filterFn!(mockRow, 'sources', [
        SocialMediaSource.YOUTUBE_VIDEO,
        SocialMediaSource.X_POST,
      ]),
    ).toBe(true);
  });

  it('filters status correctly', () => {
    const filterFn = getFilterFn('status');
    expect(filterFn).toBeDefined();

    const mockRow = {
      getValue: () => Status.COMPLETED,
    } as unknown as Row<ReportForList>;

    // Filter selects COMPLETED -> Should match
    expect(filterFn!(mockRow, 'status', [Status.COMPLETED])).toBe(true);

    // Filter selects FAILED -> Should NOT match
    expect(filterFn!(mockRow, 'status', [Status.FAILED])).toBe(false);

    // Filter selects COMPLETED and FAILED -> Should match
    expect(
      filterFn!(mockRow, 'status', [Status.COMPLETED, Status.FAILED]),
    ).toBe(true);
  });

  it('filters analysis correctly', () => {
    // Analysis column has id 'Analysis' and accessorKey 'dataOutput'
    const filterFn = getFilterFn('Analysis'); // Find by ID

    // If not found by ID, try accessorKey if ID wasn't set on the defined object (but we set it)
    // Actually in columns.tsx: { accessorKey: 'dataOutput', id: 'Analysis', ... }

    expect(filterFn).toBeDefined();

    const mockRow = {
      getValue: () => 'SENTIMENT_SCORE',
    } as unknown as Row<ReportForList>;

    expect(filterFn!(mockRow, 'dataOutput', ['SENTIMENT_SCORE'])).toBe(true);
    expect(filterFn!(mockRow, 'dataOutput', ['SHARE_OF_VOICE'])).toBe(false);
  });
});
