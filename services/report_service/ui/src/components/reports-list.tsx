'use client';

import {useRouter} from 'next/navigation';
import {format} from 'date-fns';
import {
  SentimentReport,
  ReportForList,
  Status,
  SocialMediaSource,
} from '@/lib/types';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {Card, CardContent} from '@/components/ui/card';
import {Badge} from '@/components/ui/badge';
import {FileWarning} from 'lucide-react';
import {cn} from '@/lib/utils';
import {sourceConfiguration} from '@/lib/sources';
import {SourceIcon} from './source-icon';

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
 * Renders a list of reports.
 * @param reports The reports to render.
 * @returns The reports list component.
 */
export function ReportsList({reports}: {reports: ReportForList[]}) {
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

  const handleRowClick = (report: SentimentReport) => {
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

  return (
    <Card>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[150px]">Report ID</TableHead>
              <TableHead className="w-[200px]">Topic</TableHead>
              <TableHead>Analysis</TableHead>
              <TableHead>Sources</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Date Range</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reports.map(report => (
              <TableRow
                key={report.reportId}
                onClick={() => handleRowClick(report)}
                className={cn(
                  report.status === 'FAILED'
                    ? 'opacity-50 cursor-not-allowed'
                    : 'cursor-pointer',
                )}
                title={
                  report.status === 'COMPLETED'
                    ? 'View report'
                    : report.status === 'FAILED'
                      ? 'Report failed'
                      : 'View pending report'
                }
              >
                <TableCell className="font-mono text-xs text-muted-foreground">
                  {report.reportId}
                </TableCell>
                <TableCell className="font-medium">{report.topic}</TableCell>
                <TableCell className="capitalize text-muted-foreground">
                  {report.dataOutput?.replace(/_/g, ' ')}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2 flex-wrap">
                    {report.sources.map((source, index) => {
                      const config =
                        sourceConfiguration[source as SocialMediaSource];
                      if (!config) return null;
                      return (
                        <Badge
                          variant="outline"
                          key={`${source}-${index}`}
                          className="flex items-center gap-1.5 py-0.5 px-2"
                        >
                          <SourceIcon source={source as SocialMediaSource} />
                          <span className="capitalize text-xs">
                            {config.label}
                          </span>
                        </Badge>
                      );
                    })}
                  </div>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={statusColors[report.status || 'NEW']}
                    className="capitalize"
                  >
                    {report.status?.replace(/_/g, ' ')}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {report.startTime && report.endTime && (
                    <>
                      {format(new Date(report.startTime), 'MMM d')}
                      {' - '}
                      {format(new Date(report.endTime), 'MMM d, yyyy')}
                    </>
                  )}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {report.createdOn &&
                    format(new Date(report.createdOn), 'MMM d, yyyy, h:mm a')}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
