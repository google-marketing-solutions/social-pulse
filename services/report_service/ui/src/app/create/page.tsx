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

import {CreateReportForm} from '@/components/create-report-form';

/**
 * The page to create a new report.
 * @return The create report page.
 */
export default function CreateReportPage() {
  return (
    <div className="container mx-auto max-w-2xl p-4 md:py-12">
      <div className="flex flex-col gap-4 text-center">
        <h1 className="font-headline text-4xl font-bold tracking-tighter">
          Create a New Analysis
        </h1>
        <p className="text-muted-foreground">
          Define your topic and sources to generate a social media report.
        </p>
      </div>
      <div className="mt-8">
        <CreateReportForm />
      </div>
    </div>
  );
}
