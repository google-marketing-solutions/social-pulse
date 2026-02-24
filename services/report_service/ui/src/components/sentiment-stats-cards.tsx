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

import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card';
import {OverallSentiment} from '@/lib/types';
import {ChartConfig} from '@/components/ui/chart';

const chartConfig = {
  positive: {
    label: 'Positive',
    color: 'hsl(var(--chart-2))',
  },
  neutral: {
    label: 'Neutral',
    color: 'hsl(var(--chart-4))',
  },
  negative: {
    label: 'Negative',
    color: 'hsl(var(--chart-5))',
  },
} satisfies ChartConfig;

interface SentimentStatsCardsProps {
  /** The overall sentiment data used to populate the stats. */
  overallSentiment: OverallSentiment;
  /** The label for the item count (e.g., 'Videos', 'Comments'). */
  itemLabel?: string;
  /** The label for the metrics (e.g., 'Views', 'Comments'). */
  metricLabel?: string;
}

/**
 * Displays statistical cards summarizing the overall sentiment of a report.
 *
 * This component renders two main cards:
 * 1. "Analysis Stats": Shows the total number of items and the total number
 *    of metrics.
 * 2. "Sentiment Distribution": Shows a percentage breakdown of metrics across
 *    positive, neutral, and negative sentiments.
 *
 * @param props - The component props.
 * @returns The rendered sentiment stats cards.
 */
export function SentimentStatsCards({
  overallSentiment,
  itemLabel = 'Items',
  metricLabel = 'Views',
}: SentimentStatsCardsProps) {
  const totalViews =
    overallSentiment.positive +
    overallSentiment.neutral +
    overallSentiment.negative;

  const items = [
    {
      label: 'Positive',
      value: overallSentiment.positive,
      color: chartConfig.positive.color,
    },
    {
      label: 'Neutral',
      value: overallSentiment.neutral,
      color: chartConfig.neutral.color,
    },
    {
      label: 'Negative',
      value: overallSentiment.negative,
      color: chartConfig.negative.color,
    },
  ];

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Analysis Stats</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex flex-col gap-1">
            <span className="text-sm font-medium text-muted-foreground">
              Total {itemLabel}
            </span>
            <span className="text-2xl font-bold">
              {overallSentiment.itemCount?.toLocaleString() ?? 'N/A'}
            </span>
          </div>
          {itemLabel !== metricLabel && (
            <div className="flex flex-col gap-1">
              <span className="text-sm font-medium text-muted-foreground">
                Total {metricLabel}
              </span>
              <span className="text-2xl font-bold">
                {totalViews.toLocaleString()}
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Sentiment Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <span className="text-sm font-medium text-muted-foreground">
              {metricLabel} Breakdown
            </span>
            <div className="grid grid-cols-[1fr_auto_auto] gap-x-4 gap-y-2 text-sm">
              {items.map(item => {
                const percentage =
                  totalViews > 0 ? (item.value / totalViews) * 100 : 0;

                return (
                  <div key={item.label} className="contents">
                    <span className="flex items-center gap-2">
                      <div
                        className="h-3 w-3 rounded-full"
                        style={{backgroundColor: item.color}}
                      />
                      {item.label}
                    </span>
                    <span className="justify-self-end text-muted-foreground tabular-nums text-right">
                      {percentage.toFixed(3)}%
                    </span>
                    <span className="font-medium tabular-nums text-right">
                      {item.value.toLocaleString()}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  );
}
