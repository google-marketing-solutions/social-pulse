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
 * @param filters Optional filters to apply to the report analysis results.
 * @return A promise that resolves to the report, or undefined if not found.
 */
export async function getReportById(
  id: string,
  filters?: {
    channelTitle?: string;
    startDate?: string;
    endDate?: string;
    excludedChannels?: string[];
  },
): Promise<SentimentReport | undefined> {
  try {
    const report = await apiGetReportsById(id, filters);
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

    // Defaulting to true for SENTIMENT_SCORE and false for SHARE_OF_VOICE
    includeJustifications: dataOutput === 'SENTIMENT_SCORE',

    // Defaulting to BQ_TABLE for now, as it's not in the form
    reportArtifactType: ReportArtifactType.BQ_TABLE,

    // Defaulting to empty array for now, as it's not in the form
    datasets: [],
  };

  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await apiCreateReport(payload);

    revalidatePath('/');
    revalidatePath('/create');

    return {success: true, message: 'Report created successfully.'};
  } catch (error) {
    console.error('API Error:', error);
    return {success: false, message: 'Network error creating report.'};
  }
}

/**
 * Fetches the list of channels available for a report.
 * @param id The ID of the report.
 * @return A promise that resolves to a list of channel names.
 */
export async function getReportChannels(
  id: string,
  query?: string,
): Promise<string[]> {
  const {getReportChannels: apiGetReportChannels} = await import('./api');
  try {
    return await apiGetReportChannels(id, query);
  } catch (error) {
    console.error(`Failed to fetch channels for report ${id}:`, error);
    return [];
  }
}
