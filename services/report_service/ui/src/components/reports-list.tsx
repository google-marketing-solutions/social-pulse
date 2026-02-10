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

import {useRouter} from 'next/navigation';
import {ReportForList, Status, SocialMediaSource} from '@/lib/types';
import {DataTable} from '@/components/ui/data-table';
import {columns} from '@/components/reports/columns';
import {Card, CardContent} from '@/components/ui/card';
import {FileWarning} from 'lucide-react';

/**
 * Renders a list of reports.
 * @param reports The reports to render.
 * @return The reports list component.
 */
import {
  CheckCircle2,
  Circle,
  Timer,
  XCircle,
  Video,
  MessageSquare,
  BarChart,
  PieChart,
} from 'lucide-react';
import {SentimentDataType} from '@/lib/types';

const statusOptions = [
  {
    value: Status.NEW,
    label: 'New',
    icon: Circle,
  },
  {
    value: Status.COLLECTING_DATA,
    label: 'Collecting Data',
    icon: Timer,
  },
  {
    value: Status.DATA_COLLECTED,
    label: 'Data Collected',
    icon: CheckCircle2,
  },
  {
    value: Status.GENERATING_REPORT,
    label: 'Generating Report',
    icon: Timer,
  },
  {
    value: Status.COMPLETED,
    label: 'Completed',
    icon: CheckCircle2,
  },
  {
    value: Status.FAILED,
    label: 'Failed',
    icon: XCircle,
  },
];

const analysisOptions = [
  {
    value: SentimentDataType.SENTIMENT_SCORE,
    label: 'Sentiment Score',
    icon: BarChart,
  },
  {
    value: SentimentDataType.SHARE_OF_VOICE,
    label: 'Share of Voice',
    icon: PieChart,
  },
];

const sourceOptions = [
  {
    value: SocialMediaSource.YOUTUBE_VIDEO,
    label: 'YouTube Videos',
    icon: Video,
  },
  {
    value: SocialMediaSource.YOUTUBE_COMMENT,
    label: 'YouTube Comments',
    icon: MessageSquare,
  },
  // {
  //   value: SocialMediaSource.REDDIT_POST,
  //   label: 'Reddit Posts',
  //   icon: MessageSquare,
  // },
  // {
  //   value: SocialMediaSource.X_POST,
  //   label: 'X Posts',
  //   icon: Twitter,
  // },
  // {
  //   value: SocialMediaSource.APP_STORE_REVIEW,
  //   label: 'App Store Reviews',
  //   icon: AppWindow,
  // },
];

interface ReportsListProps {
  /** Array of report objects to display. */
  reports: ReportForList[];
}

/**
 * Renders a list of reports with filtering and sorting capabilities.
 * Displays a "No reports found" message if the reports array is empty.
 *
 * @return The reports list component.
 */
export function ReportsList({reports}: ReportsListProps) {
  const router = useRouter();

  if (reports.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center text-muted-foreground">
          <FileWarning className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium">No reports found</h3>
          <p className="mt-1 text-sm">Create a new analysis to get started.</p>
        </CardContent>
      </Card>
    );
  }

  const handleRowClick = (report: ReportForList) => {
    if (
      report.status === 'COMPLETED' ||
      report.status === 'NEW' ||
      report.status === 'COLLECTING_DATA' ||
      report.status === 'DATA_COLLECTED' ||
      report.status === 'GENERATING_REPORT'
    ) {
      router.push(`/reports/${report.reportId}`);
    }
  };

  const facetedFilters = [
    {
      columnId: 'status',
      title: 'Status',
      options: statusOptions,
    },
    {
      columnId: 'Analysis',
      title: 'Analysis',
      options: analysisOptions,
    },
    {
      columnId: 'sources',
      title: 'Sources',
      options: sourceOptions,
    },
  ];

  return (
    <Card>
      <CardContent className="p-6">
        <DataTable
          columns={columns}
          data={reports}
          onRowClick={handleRowClick}
          facetedFilters={facetedFilters}
          defaultSorting={[{id: 'createdOn', desc: true}]}
        />
      </CardContent>
    </Card>
  );
}
