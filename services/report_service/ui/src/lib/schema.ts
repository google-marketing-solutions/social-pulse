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
