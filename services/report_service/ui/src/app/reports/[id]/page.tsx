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
import {getReportById} from '@/lib/actions';
import {notFound} from 'next/navigation';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import {Badge} from '@/components/ui/badge';
import {format} from 'date-fns';
import {BarChart, PieChart, Clock, CalendarDays, Info} from 'lucide-react';
import {ReportFilters} from '@/components/report-filters';
import {ReportSentimentCharts} from '@/components/report-sentiment-charts';
import {ReportShareOfVoiceCharts} from '@/components/report-share-of-voice-charts';
import {ReportJustificationCharts} from '@/components/report-justification-charts';
import {Alert, AlertDescription, AlertTitle} from '@/components/ui/alert';
import {
  SentimentReport,
  SocialMediaSource,
  Status,
  SentimentDataType,
  SourceAnalysisResult,
  ShareOfVoiceResult,
} from '@/lib/types';
import {Separator} from '@/components/ui/separator';
import {sourceConfiguration} from '@/lib/sources';

const PendingState = ({status}: {status?: Status}) => (
  <div className="relative col-span-full rounded-lg border bg-card text-card-foreground shadow-sm">
    <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 rounded-lg bg-background/80 backdrop-blur-sm">
      <Clock className="h-12 w-12 text-muted-foreground" />
      <h2 className="text-xl font-semibold">
        Analysis is {status?.replace(/_/g, ' ')}
      </h2>
      <p className="text-muted-foreground">
        The report is currently being generated. Please check back later.
      </p>
    </div>
    <div className="blur-sm">
      <CardHeader>
        <CardTitle>Results</CardTitle>
        <CardDescription>This data is not yet available.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full bg-muted rounded-md" />
      </CardContent>
    </div>
  </div>
);

/**
 * Renders the Report Detail Page.
 *
 * This component fetches and displays the details of a specific report.
 * It uses the report ID from the URL parameters to fetch the data.
 * It also supports optional filtering via search parameters.
 *
 * @param params - Promise resolving to an object containing the route
 *  parameters (e.g., `id`).
 * @param searchParams - Promise resolving to an object containing query
 *  parameters for filtering (e.g., `startDate`, `endDate`).
 * @returns A Promise that resolves to the rendered Report Detail Page
 *  component.
 */
export default async function ReportDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{id: string}>;
  searchParams: Promise<{
    channelTitle?: string;
    startDate?: string;
    endDate?: string;
    excludedChannels?: string | string[];
  }>;
}) {
  const resolvedParams = await params;
  const resolvedSearchParams = await searchParams;
  const reportId = resolvedParams.id;

  const filters = {
    channelTitle: resolvedSearchParams.channelTitle,
    startDate: resolvedSearchParams.startDate,
    endDate: resolvedSearchParams.endDate,
    excludedChannels:
      typeof resolvedSearchParams.excludedChannels === 'string'
        ? [resolvedSearchParams.excludedChannels]
        : resolvedSearchParams.excludedChannels,
  };

  const report: SentimentReport | undefined = await getReportById(
    reportId,
    filters,
  );

  if (!report) {
    notFound();
  }

  const renderCharts = () => {
    return (
      <div className="flex flex-col gap-8">
        {report.sources.map(source => {
          const config = sourceConfiguration[source as SocialMediaSource];
          if (!config) return null;

          const sourceResult = report.analysisResults?.[source];

          return (
            <div key={source} className="flex flex-col gap-4">
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0">{config.icon}</div>
                <h2 className="font-headline text-2xl font-semibold tracking-tight">
                  {config.label}
                </h2>
              </div>
              <Separator />
              {/* Impact Measurement Card */}
              <>
                <h3 className="font-headline text-xl font-semibold tracking-tight mb-3">
                  Analysis Summary
                </h3>
                {source === SocialMediaSource.YOUTUBE_VIDEO && (
                  <div className="w-full mb-4">
                    <Alert className="bg-blue-50 border-blue-200 text-blue-900">
                      <Info className="h-4 w-4 text-blue-900" />
                      <AlertTitle className="font-headline text-lg font-semibold tracking-tight text-blue-900">
                        Using Views to measure impact
                      </AlertTitle>
                      <AlertDescription className="text-blue-800">
                        When analyzing YouTube videos, we use views as a proxy
                        for impact. This allows us to compare the reach of
                        different videos and understand how they are performing
                        in terms of influencing the conversation. For the
                        purposes of analyzing YouTube videos, a view represents
                        when a user{' '}
                        <b>watches at least 30 seconds of a video</b>.
                      </AlertDescription>
                    </Alert>
                  </div>
                )}

                {report.dataOutput === SentimentDataType.SENTIMENT_SCORE && (
                  <ReportSentimentCharts
                    result={sourceResult as SourceAnalysisResult}
                    itemLabel={
                      source === SocialMediaSource.YOUTUBE_VIDEO
                        ? 'Videos'
                        : 'Comments'
                    }
                    metricLabel={
                      source === SocialMediaSource.YOUTUBE_VIDEO
                        ? 'Views'
                        : 'Comments'
                    }
                  />
                )}

                {report.dataOutput === SentimentDataType.SHARE_OF_VOICE && (
                  <ReportShareOfVoiceCharts
                    result={sourceResult as ShareOfVoiceResult}
                    itemLabel={
                      source === SocialMediaSource.YOUTUBE_VIDEO
                        ? 'Videos'
                        : 'Comments'
                    }
                    metricLabel={
                      source === SocialMediaSource.YOUTUBE_VIDEO
                        ? 'Views'
                        : 'Comments'
                    }
                  />
                )}
              </>

              {report.dataOutput === SentimentDataType.SENTIMENT_SCORE &&
                (sourceResult as SourceAnalysisResult)
                  ?.justificationBreakdown && (
                  <>
                    <h3 className="font-headline text-xl font-semibold tracking-tight mb-3 mt-6">
                      Justifications
                    </h3>
                    <ReportJustificationCharts
                      breakdown={
                        (sourceResult as SourceAnalysisResult)
                          .justificationBreakdown!
                      }
                      categories={
                        (sourceResult as SourceAnalysisResult)
                          .justificationCategories
                      }
                      metricLabel={
                        source === SocialMediaSource.YOUTUBE_VIDEO
                          ? 'Views'
                          : 'Comments Published'
                      }
                    />
                  </>
                )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4 md:py-12">
      <div className="flex flex-col gap-8">
        <div className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
          <h1 className="font-headline text-4xl font-bold tracking-tighter">
            {report.topic}
          </h1>
          <Badge className="capitalize text-sm py-1 px-3">
            {report.status?.replace(/_/g, ' ')}
          </Badge>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Analysis Type
              </CardTitle>
              {report.dataOutput === SentimentDataType.SENTIMENT_SCORE ? (
                <BarChart className="h-4 w-4 text-muted-foreground" />
              ) : (
                <PieChart className="h-4 w-4 text-muted-foreground" />
              )}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold capitalize">
                {report.dataOutput?.replace(/_/g, ' ')}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Sources</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 flex-wrap">
                {report.sources.map(source => {
                  const config =
                    sourceConfiguration[source as SocialMediaSource];
                  if (!config) return null;
                  return (
                    <Badge
                      variant="outline"
                      key={source}
                      className="flex items-center gap-1.5 py-1"
                    >
                      {config.icon}
                      <span className="capitalize">{config.label}</span>
                    </Badge>
                  );
                })}
              </div>
            </CardContent>
          </Card>
          {report.startTime && report.endTime && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Date Range
                </CardTitle>
                <CalendarDays className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-lg font-semibold">
                  {format(new Date(report.startTime), 'LLL d, y')} -{' '}
                  {format(new Date(report.endTime), 'LLL d, y')}
                </div>
              </CardContent>
            </Card>
          )}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Report Created
              </CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-lg font-semibold">
                {report.createdOn &&
                  format(new Date(report.createdOn), 'LLL d, y, p')}
              </div>
            </CardContent>
          </Card>
        </div>

        {report.status !== Status.COMPLETED &&
          report.status !== Status.FAILED && (
            <PendingState status={report.status} />
          )}

        {report.status === Status.COMPLETED && (
          <>
            <ReportFilters
              reportId={reportId}
              excludedChannels={filters.excludedChannels || []}
              defaultStartDate={report.startTime}
              defaultEndDate={report.endTime}
            />
            {renderCharts()}
          </>
        )}
      </div>
    </div>
  );
}
