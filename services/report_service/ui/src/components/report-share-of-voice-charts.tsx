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

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from '@/components/ui/chart';
import {
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Label,
} from 'recharts';
import {SentimentStatsCards} from '@/components/sentiment-stats-cards';
import {ShareOfVoiceResult} from '@/lib/types';

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

function formatNumber(value: number) {
  if (value === 0) return '0';
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1).replace(/\.0$/, '')}M`;
  }
  if (value >= 99000) {
    return `${(value / 1000).toFixed(0)}K`;
  }
  return value.toLocaleString();
}

export function ReportShareOfVoiceCharts({
  result,
}: {
  result: ShareOfVoiceResult;
  metricLabel?: string;
}) {
  console.log('ReportShareOfVoiceCharts result:', result);
  if (!result?.shareOfVoice) {
    console.log('ReportShareOfVoiceCharts: No shareOfVoice data found');
    return null;
  }

  const sortedData = [...result.shareOfVoice]
    .sort((a, b) => {
      const totalA = a.positive + a.neutral + a.negative;
      const totalB = b.positive + b.neutral + b.negative;
      return totalB - totalA;
    })
    .slice(0, 15);

  return (
    <div className="grid gap-4 lg:grid-cols-4">
      <div className="flex flex-col gap-4 lg:col-span-1">
        {result.overallSentiment && (
          <SentimentStatsCards overallSentiment={result.overallSentiment} />
        )}
      </div>

      <Card className="lg:col-span-3">
        <CardHeader>
          <CardTitle>Share of Voice</CardTitle>
          <CardDescription>
            Top 15 topics by total engagement, with sentiment breakdown.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer config={chartConfig} className="h-[500px] w-full">
            <ResponsiveContainer>
              <BarChart
                data={sortedData}
                layout="vertical"
                margin={{top: 5, right: 30, left: 30, bottom: 20}}
              >
                <CartesianGrid horizontal={false} />
                <YAxis
                  dataKey="name"
                  type="category"
                  tickLine={false}
                  axisLine={false}
                  tickMargin={10}
                  width={120}
                />
                <XAxis type="number" tickFormatter={formatNumber}>
                  <Label value="Views" position="bottom" offset={0} />
                </XAxis>
                <ChartTooltip
                  cursor={false}
                  content={<ChartTooltipContent indicator="dot" />}
                />
                <Bar
                  dataKey="positive"
                  stackId="a"
                  fill="var(--color-positive)"
                />
                <Bar
                  dataKey="neutral"
                  stackId="a"
                  fill="var(--color-neutral)"
                />
                <Bar
                  dataKey="negative"
                  stackId="a"
                  fill="var(--color-negative)"
                />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        </CardContent>
      </Card>
    </div>
  );
}
