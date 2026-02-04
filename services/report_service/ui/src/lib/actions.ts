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

'use server';

import path from 'path';
import fs from 'fs/promises';
import {revalidatePath} from 'next/cache';
import {z} from 'zod';

import {createReportSchema} from './schema';
import {SentimentReport, SocialMediaSource, ReportArtifactType} from './types';

type CreateReportState = {
  errors?: z.inferFlattenedErrors<typeof createReportSchema>['fieldErrors'];
  message?: string;
  success?: boolean;
};

import {
  createReport as apiCreateReport,
  getReports as apiGetReports,
  getReportById as apiGetReportsById,
} from './api';

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

/**
 * Fetches all reports.
 * @return A promise that resolves to an array of reports.
 */
export async function getReports(): Promise<SentimentReport[]> {
  return await apiGetReports();
}

/**
 * Fetches a report by its ID.
 * @param id The ID of the report to fetch.
 * @return A promise that resolves to the report, or undefined if not found.
 */
export async function getReportById(
  id: string,
): Promise<SentimentReport | undefined> {
  try {
    const report = await apiGetReportsById(id);
    return report;
  } catch (error) {
    console.error(`Failed to fetch report with id ${id}:`, error);
    return undefined;
  }
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
    dataOutput,
    dateRange,
    // scheduleType, // Removed
    // scheduleFrequencyWeeks, // Removed
  } = validatedFields.data;

  const payload = {
    topic,
    sources: sources as SocialMediaSource[],
    dataOutput,
    startTime: dateRange?.from
      ? new Date(dateRange.from).toISOString()
      : undefined,
    endTime: dateRange?.to ? new Date(dateRange.to).toISOString() : undefined,
    // Defaulting to false for now, as it's not in the form
    includeJustifications: false,
    // Defaulting to BQ_TABLE for now, as it's not in the form
    reportArtifactType: ReportArtifactType.BQ_TABLE,
    // Defaulting to empty array for now, as it's not in the form
    datasets: [],
  };

  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const newReportWithId: SentimentReport = await apiCreateReport(payload);

    const reports = await readData();
    reports.push(newReportWithId);
    await writeData(reports);

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
