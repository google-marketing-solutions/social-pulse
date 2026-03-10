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
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {Progress} from '@/components/ui/progress';
import {
  JustificationBreakdown,
  JustificationItem,
  JustificationCategoryMetadataItem,
} from '@/lib/types';

function JustificationList({
  data,
  title,
  description,
  colorClass,
  metricLabel,
  hoveredCategory,
  onHover,
}: {
  data: JustificationItem[];
  title: string;
  description?: string;
  colorClass: string;
  metricLabel: string;
  metadata?: JustificationCategoryMetadataItem[];
  hoveredCategory: string | null;
  onHover: (category: string | null) => void;
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
        <div className="flex justify-between items-start">
          <div>
            <CardTitle>{title}</CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          <div className="text-sm text-muted-foreground mr-2 font-medium">
            {metricLabel} (% of total)
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1">
        <div className="space-y-4">
          {data.map((item, index) => {
            const percentage = total > 0 ? (item.count / total) * 100 : 0;
            const isHovered = hoveredCategory === item.category;

            return (
              <div
                key={index}
                className={`space-y-1 p-2 -mx-2 rounded-md transition-colors ${
                  isHovered
                    ? 'bg-blue-100/50 dark:bg-blue-900/30'
                    : 'hover:bg-muted/40'
                }`}
                onMouseEnter={() => onHover(item.category)}
                onMouseLeave={() => onHover(null)}
              >
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center min-w-0">
                    <span
                      className="font-medium truncate mr-1"
                      title={item.category}
                    >
                      {item.category}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 text-muted-foreground whitespace-nowrap ml-2">
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
 * Renders a list of cards for each category metadata.
 */
function CategoryMetadataCards({
  metadata,
  hoveredCategory,
  onHover,
}: {
  metadata: JustificationCategoryMetadataItem[];
  hoveredCategory: string | null;
  onHover: (category: string | null) => void;
}) {
  if (!metadata?.length) return null;

  return (
    <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 mb-8">
      {metadata.map((item, index) => {
        const isHovered = hoveredCategory === item.categoryName;
        return (
          <Card
            key={index}
            className={`flex flex-col transition-colors border-2 ${
              isHovered
                ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
                : 'border-transparent'
            }`}
            onMouseEnter={() => onHover(item.categoryName)}
            onMouseLeave={() => onHover(null)}
          >
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">
                {item.categoryName}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {item.definition}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

/**
 * Renders the justification breakdown and category metadata cards.
 */
export function ReportJustificationCharts({
  breakdown,
  metricLabel = 'Views',
  categories = [],
}: {
  breakdown: JustificationBreakdown;
  metricLabel?: string;
  categories?: JustificationCategoryMetadataItem[];
}) {
  const [hoveredCategory, setHoveredCategory] = useState<string | null>(null);

  if (
    !breakdown.positive?.length &&
    !breakdown.negative?.length &&
    !breakdown.neutral?.length
  ) {
    return null;
  }

  return (
    <div className="flex flex-col gap-4">
      <CategoryMetadataCards
        metadata={categories}
        hoveredCategory={hoveredCategory}
        onHover={setHoveredCategory}
      />
      <div className="grid gap-4 md:grid-cols-2">
        <JustificationList
          data={breakdown.positive}
          title="Positive Justifications"
          description="Categories driving positive sentiment"
          colorClass="bg-[hsl(var(--chart-2))]"
          metricLabel={metricLabel}
          metadata={categories}
          hoveredCategory={hoveredCategory}
          onHover={setHoveredCategory}
        />
        <JustificationList
          data={breakdown.negative}
          title="Negative Justifications"
          description="Categories driving negative sentiment"
          colorClass="bg-[hsl(var(--chart-5))]"
          metricLabel={metricLabel}
          metadata={categories}
          hoveredCategory={hoveredCategory}
          onHover={setHoveredCategory}
        />
      </div>
    </div>
  );
}
