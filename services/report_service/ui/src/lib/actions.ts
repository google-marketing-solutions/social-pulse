'use server';

import fs from 'fs/promises';
import path from 'path';
import {revalidatePath} from 'next/cache';
import {z} from 'zod';

import {createReportSchema} from './schema';
import {
  SentimentReport,
  Status,
  ReportArtifactType,
  SocialMediaSource,
  SentimentDataType,
  SentimentReportDataset,
} from './types';

type CreateReportState = {
  errors?: z.inferFlattenedErrors<typeof createReportSchema>['fieldErrors'];
  message?: string;
  success?: boolean;
};

// --- MOCK DATA IMPLEMENTATION ---
// The following functions (readData, writeData) are for mocking a database
// using a local JSON file.  When you connect to a real database, you can remove
// these functions.

const dataFilePath = path.join(process.cwd(), 'src', 'lib', 'data.json');

async function readData(): Promise<SentimentReport[]> {
  try {
    const fileContent = await fs.readFile(dataFilePath, 'utf-8');
    const data = JSON.parse(fileContent);
    // Always sort by creation date descending
    return data.sort(
      (a: SentimentReport, b: SentimentReport) =>
        new Date(b.createdOn || 0).getTime() -
        new Date(a.createdOn || 0).getTime(),
    );
  } catch (error) {
    if (error instanceof Error && 'code' in error && error.code === 'ENOENT') {
      // If the file doesn't exist, create it with an empty array
      await writeData([]);
      return [];
    }
    console.error('Failed to read data file:', error);
    return [];
  }
}

async function writeData(data: SentimentReport[]) {
  try {
    const sortedData = data.sort(
      (a, b) =>
        new Date(b.createdOn || 0).getTime() -
        new Date(a.createdOn || 0).getTime(),
    );
    await fs.writeFile(dataFilePath, JSON.stringify(sortedData, null, 2));
  } catch (error) {
    console.error('Failed to write data file:', error);
  }
}

// --- MOCK API SERVICE ---
// This function simulates a backend API call to create a report.
// TODO: Replace this with your actual API call.
async function _mockApiServiceCreateReport(
  reportData: Omit<
    SentimentReport,
    | 'reportId'
    | 'createdOn'
    | 'lastUpdatedOn'
    | 'status'
    | 'datasets'
    | 'reportArtifactType'
    | 'reportArtifactUri'
    | 'analysisResults'
  >,
): Promise<SentimentReport> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 500));

  // Simulate the backend generating a unique ID and returning the full report
  // object.
  const now = new Date();
  const newReport: SentimentReport = {
    ...reportData,
    reportId: `rep_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    createdOn: now.toISOString(),
    lastUpdatedOn: now.toISOString(),
    status: Status.NEW,
    datasets: [],
    reportArtifactType: ReportArtifactType.BQ_TABLE,
  };
  return newReport;
}

// --- SERVER ACTIONS ---
// These are the functions your components call.
// You will need to replace the mock data logic inside these functions with your
// real backend calls.

/**
 * Fetches all reports.
 * @return A promise that resolves to an array of reports.
 */
export async function getReports(): Promise<SentimentReport[]> {
  // TODO: Replace this with your actual database/API call to fetch all reports.
  // TODO: Add unit tests verifying the data returned by the API call is
  //       properly loaded into data objects.
  return await readData();
}

/**
 * Fetches a report by its ID.
 * @param id The ID of the report to fetch.
 * @return A promise that resolves to the report, or undefined if not found.
 */
export async function getReportById(
  id: string,
): Promise<SentimentReport | undefined> {
  // TODO: Replace this with your actual database/API call to fetch a single
  //       report by its ID.
  // TODO: Add unit tests verifying the data returned by the API call is
  //       properly loaded into data objects.
  const reports = await readData();
  const report = reports.find(report => report.reportId === id);
  return report;
}

/**
 * Creates a new report.
 * @param prevState The previous state.
 * @param data The form data.
 * @return A promise that resolves to the new state.
 */
export async function createReport(
  prevState: CreateReportState,
  data: z.infer<typeof createReportSchema>,
) {
  const validatedFields = createReportSchema.safeParse(data);

  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
      message: 'Error submitting form. Please check the fields.',
      success: false,
    };
  }

  const {
    topic,
    sources,
    analysisType, // This needs to be mapped to data_output
    dateRange,
    // scheduleType, // Removed
    // scheduleFrequencyWeeks, // Removed
  } = validatedFields.data;

  // This is the object that will be sent to your backend.
  const newReportData: Omit<
    SentimentReport,
    | 'reportId'
    | 'createdOn'
    | 'lastUpdatedOn'
    | 'status'
    | 'datasets'
    | 'reportArtifactType'
    | 'reportArtifactUri'
    | 'analysisResults'
  > = {
    topic,
    sources: sources as SocialMediaSource[],
    dataOutput:
      analysisType === 'sentiment'
        ? SentimentDataType.SENTIMENT_SCORE
        : SentimentDataType.SHARE_OF_VOICE,
    startTime: dateRange?.from
      ? new Date(dateRange.from).toISOString()
      : undefined,
    endTime: dateRange?.to ? new Date(dateRange.to).toISOString() : undefined,
    // Defaulting to false for now, as it's not in the form
    includeJustifications: false,
  };

  try {
    // TODO: Replace this mock API call with your actual backend call.
    // TODO: Add unit tests verifying the API call uses the correct data from
    //       the form.
    // The call should return the newly created report, including the ID
    // generated by the server.
    const newReportWithId = await _mockApiServiceCreateReport(newReportData);

    // TODO: Once you have a real backend, you can remove the following lines
    // that write to the mock data file.
    const reports = await readData();
    reports.push(newReportWithId);
    await writeData(reports);
    // --- End of mock data logic ---

    revalidatePath('/');
    revalidatePath('/create');

    return {success: true, message: 'Report created successfully.'};
  } catch (error) {
    console.error('API Error:', error);
    return {success: false, message: 'Network error creating report.'};
  }
}

/**
 * Updates a report.
 * @param reportId The ID of the report to update.
 * @param updates The updates to apply.
 * @return A promise that resolves to the updated report, or undefined if not
 * found.
 */
export async function updateReport(
  reportId: string,
  updates: Partial<SentimentReport>,
): Promise<SentimentReport | undefined> {
  // TODO: Replace this with your actual database/API call to update a report.
  // TODO: Add unit tests verifying the data to the API call is properly pulled
  //       from the data objects.
  const reports = await readData();
  const reportIndex = reports.findIndex(r => r.reportId === reportId);

  if (reportIndex === -1) {
    console.error(`Report with reportId ${reportId} not found.`);
    return undefined;
  }

  const updatedReport = {...reports[reportIndex], ...updates};
  reports[reportIndex] = updatedReport;
  await writeData(reports);
  // --- End of mock data logic ---

  revalidatePath('/');
  revalidatePath(`/reports/${reportId}`);

  return updatedReport;
}
