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

import {useState} from 'react';
import {
  ReportInsight,
  InsightType,
  TrendInsightContent,
  SpikeInsightContent,
} from '@/lib/types';
import {
  TrendingUp,
  Activity,
  AlertTriangle,
  Quote,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {Separator} from '@/components/ui/separator';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';

/**
 * Renders the executive insights section of a report, displaying AI-generated
 * trends and anomaly spikes. This component is useful for giving users a
 * high-level overview of the most critical patterns found in their data.
 */
// TODO(jcryan): Add UI testing for this component.
export function ReportInsightsSection({insights}: {insights: ReportInsight[]}) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!insights || insights.length === 0) return null;

  const trends = insights.filter(i => i.insightType === InsightType.TREND);
  const spikes = insights.filter(i => i.insightType === InsightType.SPIKE);

  const allTrends: TrendInsightContent['top_trends'] = trends.flatMap(
    t => (t.content as TrendInsightContent).top_trends || [],
  );
  const allSpikes: SpikeInsightContent['spikes'] = spikes.flatMap(
    s => (s.content as SpikeInsightContent).spikes || [],
  );

  const visibleTrends = isExpanded ? allTrends : allTrends.slice(0, 1);
  const visibleSpikes = isExpanded ? allSpikes : allSpikes.slice(0, 1);

  const hasValidTrends = allTrends.length > 0;
  const hasValidSpikes = allSpikes.length > 0;

  if (!hasValidTrends && !hasValidSpikes) {
    return (
      <div className="flex flex-col gap-8 my-10 animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
        <div className="flex flex-col gap-2">
          <h2 className="font-headline text-3xl font-bold tracking-tight text-slate-900 border-l-4 border-slate-900 pl-4">
            Executive Insights
          </h2>
          <p className="text-muted-foreground text-lg pl-5 max-w-3xl">
            AI-generated synthesis of key patterns and anomalies detected in
            this report.
          </p>
        </div>
        <div className="rounded-xl bg-slate-50 border border-slate-100 p-8 text-center flex flex-col items-center justify-center">
          <p className="text-slate-500 italic text-lg">
            No significant trends or anomalies are available for this report.
          </p>
        </div>
        <Separator className="mt-4 opacity-50" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8 my-10 animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      <div className="flex flex-col gap-2">
        <h2 className="font-headline text-3xl font-bold tracking-tight text-slate-900 border-l-4 border-slate-900 pl-4">
          Executive Insights
        </h2>
        <p className="text-muted-foreground text-lg pl-5 max-w-3xl">
          AI-generated synthesis of key patterns and anomalies detected in this
          report.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Trends Section */}
        {hasValidTrends && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2 mb-2 text-slate-800">
              <TrendingUp className="h-6 w-6 text-blue-600" />
              <h3 className="font-headline text-2xl font-semibold">
                Top Trends
              </h3>
            </div>
            <div className="flex flex-col gap-6">
              {visibleTrends.map((trend, j) => (
                <div
                  key={j}
                  className="group relative overflow-hidden rounded-xl bg-gradient-to-b from-white to-slate-50/50 border border-slate-200/60 p-6 shadow-sm transition-all hover:shadow-md hover:border-slate-300"
                >
                  <div className="absolute top-0 left-0 w-1 h-full bg-blue-600/80 transform origin-left transition-transform group-hover:scale-y-110"></div>
                  <h4 className="text-xl font-bold text-slate-900 mb-2 font-headline">
                    {trend.trend_title}
                  </h4>
                  <p className="text-slate-600 text-base leading-relaxed mb-4">
                    {trend.description}
                  </p>

                  {trend.justifications?.length > 0 && (
                    <div className="bg-slate-100/50 rounded-lg p-5 mt-2 border border-slate-100 relative">
                      <Quote className="absolute top-3 left-3 h-8 w-8 text-blue-200 opacity-50 -rotate-12" />
                      <p className="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-3 relative z-10 pl-5">
                        Key Drivers
                      </p>
                      <ul className="space-y-3 relative z-10">
                        {trend.justifications.map((just, k) => (
                          <li
                            key={k}
                            className="flex items-start gap-3 text-sm text-slate-700 bg-white/60 p-3 rounded-md border border-slate-100/50 shadow-sm"
                          >
                            <Quote className="h-4 w-4 text-blue-400 mt-0.5 flex-shrink-0" />
                            <span className="leading-snug italic">{just}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Spikes Section */}
        {spikes.length > 0 && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2 mb-2 text-slate-800">
              <Activity className="h-6 w-6 text-amber-600" />
              <h3 className="font-headline text-2xl font-semibold">
                Spike Analysis
              </h3>
            </div>
            <div className="flex flex-col gap-6 h-full">
              {hasValidSpikes ? (
                visibleSpikes.map((spike, j) => (
                  <div
                    key={j}
                    className="group relative overflow-hidden rounded-xl bg-gradient-to-b from-amber-50/30 to-white border border-amber-200/50 p-6 shadow-sm transition-all hover:shadow-md hover:border-amber-300/60"
                  >
                    <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full -translate-y-12 translate-x-12 transform group-hover:scale-150 transition-transform duration-500"></div>
                    <div className="flex items-start gap-2 mb-3">
                      <AlertTriangle className="h-5 w-5 text-amber-600 mt-1 flex-shrink-0" />
                      <h4 className="text-xl font-bold text-amber-950 font-headline">
                        {spike.spike_topic}
                      </h4>
                      {spike.spike_magnitude && (
                        <Badge
                          variant="outline"
                          className="ml-auto capitalize bg-amber-100/50 text-amber-800 border-amber-200"
                        >
                          {spike.spike_magnitude} impact
                        </Badge>
                      )}
                    </div>

                    {(spike.spike_trend || spike.spike_month) && (
                      <div className="flex items-center gap-2 mb-3 mt-1">
                        {spike.spike_trend && (
                          <Badge
                            variant="secondary"
                            className="text-xs capitalize bg-white/60 text-slate-600 hover:bg-white/80 border border-slate-200/60"
                          >
                            Trend: {spike.spike_trend}
                          </Badge>
                        )}
                        {spike.spike_month && (
                          <Badge
                            variant="secondary"
                            className="text-xs bg-white/60 text-slate-600 hover:bg-white/80 border border-slate-200/60"
                          >
                            Month: {spike.spike_month}
                          </Badge>
                        )}
                      </div>
                    )}

                    <div className="prose prose-sm prose-slate mb-4 text-slate-700 leading-relaxed">
                      <p>{spike.cause_analysis}</p>
                    </div>

                    {spike.primary_video_evidence?.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-amber-100/60 relative">
                        <Quote className="absolute top-4 right-2 h-10 w-10 text-amber-100 opacity-60 rotate-12" />
                        <p className="text-xs uppercase tracking-wider font-semibold text-amber-800/70 mb-3 relative z-10">
                          Primary Evidence
                        </p>
                        <ul className="space-y-3 text-sm text-slate-700 relative z-10">
                          {spike.primary_video_evidence.map((evidence, k) => (
                            <li
                              key={k}
                              className="flex items-start gap-3 bg-white/50 p-3 rounded-md border border-amber-100/50 shadow-sm"
                            >
                              <Quote className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                              <span className="italic leading-snug text-slate-700 font-medium">
                                {evidence}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="rounded-xl bg-slate-50 border border-slate-100 p-6 text-center h-full flex items-center justify-center min-h-[200px]">
                  <p className="text-slate-500 italic">
                    No significant anomalies or spikes detected in this
                    reporting period.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {(allTrends.length > 1 || allSpikes.length > 1) && (
        <div className="flex justify-center mt-8">
          <Button
            variant="outline"
            onClick={() => setIsExpanded(!isExpanded)}
            className="group px-6 py-5 rounded-full border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-all shadow-sm"
          >
            <span className="mr-2 font-medium">
              {isExpanded ? 'Show Less' : 'Show More Insights'}
            </span>
            {isExpanded ? (
              <ChevronUp className="h-4 w-4 text-slate-500 group-hover:text-slate-800 transition-colors" />
            ) : (
              <ChevronDown className="h-4 w-4 text-slate-500 group-hover:text-slate-800 transition-colors" />
            )}
          </Button>
        </div>
      )}

      <Separator className="mt-12 opacity-50" />
    </div>
  );
}
