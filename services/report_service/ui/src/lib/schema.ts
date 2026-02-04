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

import {z} from 'zod';
import {SocialMediaSource, SentimentDataType} from './types';

const reportSchemaBase = z.object({
  topic: z.string().min(3, {message: 'Topic must be at least 3 characters.'}),
  sources: z
    .array(z.nativeEnum(SocialMediaSource))
    .min(1, {message: 'Please select at least one source.'})
    .refine(arr => new Set(arr).size === arr.length, {
      message: 'Sources must be unique.',
    }),
  dataOutput: z.nativeEnum(SentimentDataType),
  dateRange: z
    .object({
      from: z.date({required_error: 'A start date is required.'}),
      to: z.date().optional(),
    })
    .optional(),
});

/**
 * The schema for creating a report.
 */
export const createReportSchema = reportSchemaBase.refine(
  data => {
    return !!data.dateRange?.from;
  },
  {
    message: 'A date range is required for reports.',
    path: ['dateRange'],
  },
);
