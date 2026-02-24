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
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {Progress} from '@/components/ui/progress';
import {JustificationBreakdown, JustificationItem} from '@/lib/types';

function JustificationList({
  data,
  title,
  description,
  colorClass,
}: {
  data: JustificationItem[];
  title: string;
  description?: string;
  colorClass: string;
}) {
  if (!data?.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>No data available</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Calculate total for percentage
  const total = data.reduce((acc, item) => acc + item.count, 0);

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="flex-1">
        <div className="space-y-4">
          {data.map((item, index) => {
            const percentage = total > 0 ? (item.count / total) * 100 : 0;
            return (
              <div key={index} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span
                    className="font-medium truncate mr-2"
                    title={item.category}
                  >
                    {item.category}
                  </span>
                  <div className="flex items-center space-x-2 text-muted-foreground whitespace-nowrap">
                    <span>{item.count.toLocaleString()}</span>
                    <span className="text-xs">({percentage.toFixed(1)}%)</span>
                  </div>
                </div>
                <Progress
                  value={percentage}
                  className="h-2"
                  indicatorClassName={colorClass}
                />
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Renders two lists for positive and negative justifications.
 */
export function ReportJustificationCharts({
  breakdown,
}: {
  breakdown: JustificationBreakdown;
}) {
  if (
    !breakdown.positive?.length &&
    !breakdown.negative?.length &&
    !breakdown.neutral?.length
  ) {
    return null;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <JustificationList
        data={breakdown.positive}
        title="Positive Justifications"
        description="Categories driving positive sentiment"
        colorClass="bg-[hsl(var(--chart-2))]"
      />
      <JustificationList
        data={breakdown.negative}
        title="Negative Justifications"
        description="Categories driving negative sentiment"
        colorClass="bg-[hsl(var(--chart-5))]"
      />
    </div>
  );
}
