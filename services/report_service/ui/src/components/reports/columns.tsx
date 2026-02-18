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
'use client';

import {ColumnDef} from '@tanstack/react-table';
import {ArrowUpDown} from 'lucide-react';
import {format} from 'date-fns';

import {Button} from '@/components/ui/button';
import {Badge} from '@/components/ui/badge';
import {ReportForList, Status, SocialMediaSource} from '@/lib/types';
import {sourceConfiguration} from '@/lib/sources';
import {SourceIcon} from '@/components/source-icon';

const statusColors: {[key in Status]: 'default' | 'secondary' | 'destructive'} =
  {
    NEW: 'secondary',
    COLLECTING_DATA: 'secondary',
    DATA_COLLECTED: 'secondary',
    GENERATING_REPORT: 'secondary',
    COMPLETED: 'default',
    FAILED: 'destructive',
  };

/**
 * Defines the columns for the reports table.
 * Each object in the array configures a column, specifying how to access the
 * data, render the header and cells, and handle sorting and filtering.
 */
export const columns: Array<ColumnDef<ReportForList>> = [
  {
    accessorKey: 'topic',
    header: ({column}) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="-ml-3"
        >
          Topic
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({row}) => <div className="font-medium">{row.getValue('topic')}</div>,
    enableGlobalFilter: true,
  },
  {
    accessorKey: 'dataOutput',
    id: 'Analysis',
    header: 'Analysis',
    cell: ({row}) => {
      const value = row.getValue('Analysis') as string;
      return (
        <div className="capitalize text-muted-foreground">
          {value?.replace(/_/g, ' ')}
        </div>
      );
    },
    filterFn: (row, id, value) => {
      return value.includes(row.getValue(id));
    },
  },
  {
    accessorKey: 'sources',
    header: 'Sources',
    cell: ({row}) => {
      const sources = row.getValue('sources') as SocialMediaSource[];
      return (
        <div className="flex items-center gap-2 flex-wrap">
          {sources.map((source, index) => {
            const config = sourceConfiguration[source];
            if (!config) return null;
            return (
              <Badge
                variant="outline"
                key={`${source}-${index}`}
                className="flex items-center gap-1.5 py-0.5 px-2"
              >
                <SourceIcon source={source} />
                <span className="capitalize text-xs">{config.label}</span>
              </Badge>
            );
          })}
        </div>
      );
    },
    filterFn: (row, id, value) => {
      const sources = row.getValue(id) as SocialMediaSource[];
      if (!value || value.length === 0) return true;
      return sources.some(source => value.includes(source));
    },
  },
  {
    accessorKey: 'status',
    header: ({column}) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="-ml-3"
        >
          Status
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({row}) => {
      const status = row.getValue('status') as Status;
      return (
        <Badge variant={statusColors[status || 'NEW']} className="capitalize">
          {status?.replace(/_/g, ' ')}
        </Badge>
      );
    },
    filterFn: (row, id, value) => {
      return value.includes(row.getValue(id));
    },
  },
  {
    accessorKey: 'startTime',
    header: ({column}) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="-ml-3"
        >
          Start Date
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({row}) => {
      const date = row.getValue('startTime') as string;
      if (!date) return null;
      return (
        <div className="text-muted-foreground">
          {format(new Date(date), 'MMM d, yyyy')}
        </div>
      );
    },
  },
  {
    accessorKey: 'endTime',
    header: ({column}) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="-ml-3"
        >
          End Date
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({row}) => {
      const date = row.getValue('endTime') as string;
      if (!date) return null;
      return (
        <div className="text-muted-foreground">
          {format(new Date(date), 'MMM d, yyyy')}
        </div>
      );
    },
  },
  {
    accessorKey: 'createdOn',
    header: ({column}) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="-ml-3"
        >
          Created
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({row}) => {
      const date = row.getValue('createdOn') as string;
      if (!date) return null;
      return (
        <div className="text-muted-foreground">
          {format(new Date(date), 'MMM d, yyyy, h:mm a')}
        </div>
      );
    },
  },
];
