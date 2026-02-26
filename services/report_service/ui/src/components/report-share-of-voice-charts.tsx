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
  Bar,
  BarChart,
  CartesianGrid,
  Label,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card';
import {
  ChartConfig,
  ChartContainer,
  ChartTooltipContent,
} from '@/components/ui/chart';
import {ShareOfVoiceResult} from '@/lib/types';

const chartConfig: ChartConfig = {
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
};

function formatYAxisTick(value: number) {
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
  metricLabel = 'Views',
}: {
  result: ShareOfVoiceResult;
  metricLabel?: string;
}) {
  if (!result?.shareOfVoice || result.shareOfVoice.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Share of Voice</CardTitle>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[400px] w-full">
          <BarChart
            data={result.shareOfVoice}
            layout="vertical"
            margin={{left: 20, right: 20, top: 20, bottom: 20}}
          >
            <CartesianGrid horizontal={false} />
            <XAxis
              type="number"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              tickFormatter={formatYAxisTick}
            >
              <Label value={metricLabel} position="bottom" offset={10} />
            </XAxis>
            <YAxis
              dataKey="name"
              type="category"
              tickLine={false}
              axisLine={false}
              tickMargin={10}
              width={150}
            />
            <Tooltip content={<ChartTooltipContent indicator="dot" />} />
            <Bar
              dataKey="positive"
              stackId="a"
              fill="var(--color-positive)"
              radius={0}
            />
            <Bar dataKey="neutral" stackId="a" fill="var(--color-neutral)" />
            <Bar
              dataKey="negative"
              stackId="a"
              fill="var(--color-negative)"
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
