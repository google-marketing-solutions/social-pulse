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

import {ReportsList} from '@/components/reports-list';
import {getReports} from '@/lib/actions';
import {Button} from '@/components/ui/button';
import Link from 'next/link';
import {PlusCircle} from 'lucide-react';
import {SentimentReport, ReportForList} from '@/lib/types';

/**
 * The page to display all reports.
 * @return The reports list page.
 */
export default async function ReportsListPage() {
  const reports: SentimentReport[] = await getReports();

  const reportsForList: ReportForList[] = reports.map(report => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const {datasets, ...rest} = report;
    return rest;
  });

  return (
    <div className="container mx-auto p-4 md:py-12">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-headline text-3xl font-bold">All Reports</h1>
        <Button asChild>
          <Link href="/create">
            <PlusCircle className="mr-2 h-4 w-4" />
            New Analysis
          </Link>
        </Button>
      </div>
      <ReportsList reports={reportsForList} />
    </div>
  );
}
