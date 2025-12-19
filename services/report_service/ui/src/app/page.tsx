import {ReportsList} from '@/components/reports-list';
import {getReports} from '@/lib/actions';
import {Button} from '@/components/ui/button';
import Link from 'next/link';
import {PlusCircle} from 'lucide-react';
import {SentimentReport, ReportForList} from '@/lib/types';

/**
 * The page to display all reports.
 * @returns The reports list page.
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
