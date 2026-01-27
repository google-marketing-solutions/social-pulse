'use client';

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Label,
  Pie,
  PieChart as RechartsPieChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

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
import {format} from 'date-fns';
import {SourceAnalysisResult} from '@/lib/types';

const chartConfig: ChartConfig = {
  positive: {label: 'Positive', color: 'hsl(var(--chart-2))'},
  neutral: {label: 'Neutral', color: 'hsl(var(--chart-4))'},
  negative: {label: 'Negative', color: 'hsl(var(--chart-5))'},
};

const RADIAN = Math.PI / 180;
function renderCustomizedLabel({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percent,
  payload,
}: {
  cx: number;
  cy: number;
  midAngle: number;
  innerRadius: number;
  outerRadius: number;
  percent: number;
  index: number;
  payload: {color: string};
}) {
  const radius = innerRadius + (outerRadius - innerRadius) * 1.6;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text
      x={x}
      y={y}
      fill={payload.color}
      textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central"
      className="font-bold"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
}

export function ReportSentimentCharts({
  result,
  metricLabel,
}: {
  result: SourceAnalysisResult;
  metricLabel: string;
}) {
  if (!result?.sentimentOverTime || !result.overallSentiment) return null;

  const overallData = [
    {
      name: 'Positive',
      value: result.overallSentiment.positive,
      color: 'hsl(var(--chart-2))',
    },
    {
      name: 'Neutral',
      value: result.overallSentiment.neutral,
      color: 'hsl(var(--chart-4))',
    },
    {
      name: 'Negative',
      value: result.overallSentiment.negative,
      color: 'hsl(var(--chart-5))',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
      <Card className="lg:col-span-4">
        <CardHeader>
          <CardTitle>Sentiment Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <ChartContainer config={chartConfig} className="h-[250px] w-full">
            <BarChart
              data={result.sentimentOverTime}
              margin={{left: 20, right: 20, top: 5, bottom: 20}}
            >
              <CartesianGrid vertical={false} />
              <YAxis
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                allowDecimals={false}
              >
                <Label
                  value={metricLabel}
                  angle={-90}
                  position="insideLeft"
                  style={{textAnchor: 'middle'}}
                />
              </YAxis>
              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tickFormatter={value => format(new Date(value), 'MMM d')}
              >
                <Label
                  value="Date Published (by week)"
                  position="bottom"
                  offset={10}
                />
              </XAxis>
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
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>
      <Card className="lg:col-span-3">
        <CardHeader>
          <CardTitle>Overall Sentiment</CardTitle>
          <CardDescription>Total distribution of sentiment.</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center">
          <ChartContainer
            config={chartConfig}
            className="mx-auto aspect-square h-[250px]"
          >
            <RechartsPieChart>
              <Tooltip content={<ChartTooltipContent hideLabel />} />
              <Pie
                data={overallData}
                dataKey="value"
                nameKey="name"
                innerRadius={60}
                outerRadius={80}
                strokeWidth={5}
                labelLine={false}
                label={renderCustomizedLabel}
              >
                {overallData.map(entry => (
                  <Cell key={`cell-${entry.name}`} fill={entry.color} />
                ))}
              </Pie>
            </RechartsPieChart>
          </ChartContainer>
        </CardContent>
      </Card>
    </div>
  );
}
