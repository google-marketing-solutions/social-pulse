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
