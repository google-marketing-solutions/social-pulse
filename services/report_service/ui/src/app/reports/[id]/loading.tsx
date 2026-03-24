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

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex flex-col w-full">
      {/* Sticky Full-Width Report Header */}
      <div className="sticky top-14 z-40 w-full bg-muted/80 backdrop-blur-md border-b shadow-sm">
        <div className="container mx-auto px-4 py-6 md:px-8 flex flex-col gap-6">
        {/* Loading Indicator Text */}
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          <span className="text-lg font-medium">Your analysis results are loading...</span>
        </div>

        {/* Title and Badge Skeleton */}
        <div className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
          <Skeleton className="h-10 w-2/3 md:w-1/3" />
          <Skeleton className="h-6 w-24 rounded-full" />
        </div>

        {/* 4 Summary Cards Skeleton */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-4 w-4 rounded-full" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-1/2 mt-2" />
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Filters Skeleton */}
        <div className="flex gap-4 items-center">
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-10 w-24 ml-auto" />
        </div>
      </div>
      </div> {/* End Sticky Full-Width Report Header */}

      {/* Main Analysis Results Viewport */}
      <div className="container mx-auto px-4 py-8 md:px-8 md:py-12 flex flex-col gap-8">
        {/* Charts/Sources Layout Skeleton */}
        <div className="flex flex-col gap-8 mt-4">
          {[...Array(2)].map((_, sourceIdx) => (
            <div key={sourceIdx} className="flex flex-col gap-4">
              <div className="flex items-center gap-3">
                <Skeleton className="h-8 w-8 rounded-full" />
                <Skeleton className="h-8 w-48" />
              </div>

              <Skeleton className="h-px w-full my-2" />

              <Skeleton className="h-6 w-48 mb-3" />

              {/* Alert Mockup */}
              <Skeleton className="h-24 w-full rounded-lg mb-4" />

              {/* Main Chart Mockup */}
              <Card className="mb-6">
                <CardHeader>
                  <Skeleton className="h-6 w-1/4 mb-2" />
                  <Skeleton className="h-4 w-1/3" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-[300px] w-full rounded-md" />
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
