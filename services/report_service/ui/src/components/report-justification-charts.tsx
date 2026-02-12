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
import {
  ChartConfig,
  ChartContainer,
  ChartTooltipContent,
} from '@/components/ui/chart';
import {JustificationBreakdown, JustificationItem} from '@/lib/types';
import {Cell, Pie, PieChart as RechartsPieChart, Tooltip} from 'recharts';

const chartConfig: ChartConfig = {
  count: {label: 'Count'},
};

const COLORS = [
  'hsl(var(--chart-1))',
  'hsl(var(--chart-2))',
  'hsl(var(--chart-3))',
  'hsl(var(--chart-4))',
  'hsl(var(--chart-5))',
  'hsl(var(--chart-1))', // Repeat if needed
];

function wrapText(text: string, maxChars: number): string[] {
  const words = text.split(' ');
  const lines: string[] = [];
  let currentLine = words[0];

  for (let i = 1; i < words.length; i++) {
    if (currentLine.length + 1 + words[i].length <= maxChars) {
      currentLine += ' ' + words[i];
    } else {
      lines.push(currentLine);
      currentLine = words[i];
    }
  }
  lines.push(currentLine);
  return lines;
}

// Helper to compute layout with collision detection (relative to center)
function computeLabelLayout(data: JustificationItem[], outerRadius: number) {
  const total = data.reduce((acc, item) => acc + item.count, 0);
  let currentAngle = 0; // Recharts default: 0 degrees is 3 o'clock, CCW.

  const labels = data.map((item, index) => {
    const value = item.count;
    const Angle = (value / total) * 360;
    const midAngle = currentAngle + Angle / 2;
    currentAngle += Angle;

    const RADIAN = Math.PI / 180;
    // ideal Y offset at the label radius
    const labelRadius = outerRadius + 30; // Elbow distance
    // sin(-midAngle) gives Y offset (up is negative in Math, but in SVG y increases down).
    // Recharts: y = cy + r * sin(-midAngle).
    // So relative Y = r * sin(-midAngle).
    const rawY = labelRadius * Math.sin(-midAngle * RADIAN);
    const rawX = labelRadius * Math.cos(-midAngle * RADIAN);

    // Determine side based on X offset
    const isLeft = rawX < 0;

    const lineCount = wrapText(item.category, 20).length + 1; // +1 for percentage line
    const height = lineCount * 20; // Approx 20px per line (12px font + spacing)

    return {
      index,
      midAngle,
      rawY,
      isLeft,
      percent: value / total,
      category: item.category,
      adjustedY: rawY,
      height,
    };
  });

  // Separate and sort by Y
  const leftLabels = labels
    .filter(l => l.isLeft)
    .sort((a, b) => a.rawY - b.rawY);
  const rightLabels = labels
    .filter(l => !l.isLeft)
    .sort((a, b) => a.rawY - b.rawY);

  const resolveCollisions = (items: typeof labels) => {
    // Forward pass (push down)
    for (let i = 1; i < items.length; i++) {
      const prev = items[i - 1];
      const curr = items[i];

      // Calculate required spacing based on heights (half of prev + half of curr + padding)
      const spacing = prev.height / 2 + curr.height / 2 + 10;

      if (curr.adjustedY < prev.adjustedY + spacing) {
        curr.adjustedY = prev.adjustedY + spacing;
      }
    }
  };

  resolveCollisions(leftLabels);
  resolveCollisions(rightLabels);

  const layoutMap = new Map<number, (typeof labels)[0]>();
  labels.forEach(l => layoutMap.set(l.index, l));
  return layoutMap;
}

function JustificationPieChart({
  data,
  title,
  description,
}: {
  data: JustificationItem[];
  title: string;
  description?: string;
}) {
  const outerRadius = 80;
  const chartCenterY = 120; // Fixed Y position to move chart up (reduce empty space)
  const layoutMap = computeLabelLayout(data, outerRadius);

  // Calculate dynamic height based on labels
  let maxBottom = chartCenterY + outerRadius + 50; // Minimum bottom
  layoutMap.forEach(layout => {
    const bottom = chartCenterY + layout.adjustedY + (layout.height || 20);
    if (bottom > maxBottom) {
      maxBottom = bottom;
    }
  });
  const containerHeight = Math.max(300, maxBottom + 40); // Add padding

  // Custom label component wrapper
  const renderLabel = (props: {index: number; cx: number}) => {
    const {index, cx} = props;
    const cy = chartCenterY; // Use fixed CY
    const layout = layoutMap.get(index);
    if (!layout || layout.percent === 0) return null;

    // Line start (on slice)
    const RADIAN = Math.PI / 180;
    const midAngle = layout.midAngle;
    const cos = Math.cos(-RADIAN * midAngle);
    const sin = Math.sin(-RADIAN * midAngle);
    const sx = cx + outerRadius * cos;
    const sy = cy + outerRadius * sin;

    // Elbow Target
    const elbowRadius = outerRadius + 20;
    const mx = cx + elbowRadius * cos;
    const my = cy + elbowRadius * sin;

    // Label Target
    const rowY = cy + layout.adjustedY;
    // Align text at fixed offset from center
    const textXOffset = 140; // Reduced from 160 to prevent cutoff
    const textX = cx + (layout.isLeft ? -textXOffset : textXOffset);
    const textAnchor = layout.isLeft ? 'end' : 'start';

    const categoryLines = wrapText(layout.category, 20); // Wrap stricter (20 chars)
    const percentText = `(${(layout.percent * 100).toFixed(0)}%)`;

    return (
      <g>
        <path
          d={`M${sx},${sy}L${mx},${my}L${textX},${rowY}`}
          stroke="hsl(var(--foreground))"
          fill="none"
        />
        <circle
          cx={textX}
          cy={rowY}
          r={2}
          fill="hsl(var(--foreground))"
          stroke="none"
        />
        <text
          x={textX + (layout.isLeft ? -10 : 10)}
          y={rowY}
          textAnchor={textAnchor}
          fill="hsl(var(--foreground))"
          dominantBaseline="central"
          className="text-xs"
        >
          {categoryLines.map((line, i) => (
            <tspan
              key={i}
              x={textX + (layout.isLeft ? -10 : 10)}
              dy={i === 0 ? (categoryLines.length > 1 ? '-0.5em' : 0) : '1.2em'}
            >
              {line}
            </tspan>
          ))}
          <tspan
            x={textX + (layout.isLeft ? -10 : 10)}
            dy="1.2em"
            fill="hsl(var(--muted-foreground))"
          >
            {percentText}
          </tspan>
        </text>
      </g>
    );
  };

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

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="pb-4">
        <ChartContainer
          config={chartConfig}
          className="mx-auto w-full"
          style={{height: containerHeight, minHeight: '300px'}}
        >
          <RechartsPieChart>
            <Tooltip
              content={
                <ChartTooltipContent
                  nameKey="category"
                  labelKey="category"
                  indicator="dot"
                />
              }
            />
            <Pie
              data={data}
              dataKey="count"
              nameKey="category"
              cx="50%"
              cy={chartCenterY}
              innerRadius={50}
              outerRadius={outerRadius}
              label={renderLabel}
              labelLine={false} // We draw our own lines
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
            </Pie>
          </RechartsPieChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}

/**
 * Renders two pie charts for positive and negative justifications.
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
      <JustificationPieChart
        data={breakdown.positive}
        title="Positive Justifications"
        description="Categories driving positive sentiment"
      />
      <JustificationPieChart
        data={breakdown.negative}
        title="Negative Justifications"
        description="Categories driving negative sentiment"
      />
    </div>
  );
}
