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

/**
 * Types of insights that can be generated for a report.
 */
export enum InsightType {
  TREND = 'TREND',
  SPIKE = 'SPIKE',
}

/**
 * Content structure for a trend insight.
 */
export interface TrendInsightContent {
  top_trends: Array<{
    trend_title: string;
    description: string;
    justifications: string[];
  }>;
}

/**
 * Content structure for a spike insight.
 */
export interface SpikeInsightContent {
  spikes: Array<{
    spike_topic: string;
    cause_analysis: string;
    primary_video_evidence: string[];
    spike_magnitude?: string;
    spike_trend?: string;
    spike_month?: string;
  }>;
}

/**
 * Represents a single generated insight for a report.
 */
export interface ReportInsight {
  insightId?: string;
  reportId: string;
  insightType: InsightType;
  content: TrendInsightContent | SpikeInsightContent;
  rawPromptOutput?: string;
  createdOn?: string;
}

/**
 * Represents a single message in a chat conversation.
 */
export interface ChatMessage {
  role: string;
  content: string;
}

/**
 * Represents a request to chat about a report.
 */
export interface ChatRequest {
  query: string;
  history?: ChatMessage[];
}

/**
 * Represents a response from a chat query.
 */
export interface ChatResponse {
  response: string;
}

/**
 * The social media sources that can be analyzed.
 */
export enum SocialMediaSource {
  YOUTUBE_VIDEO = 'YOUTUBE_VIDEO',
  YOUTUBE_COMMENT = 'YOUTUBE_COMMENT',
  REDDIT_POST = 'REDDIT_POST',
  X_POST = 'X_POST',
  APP_STORE_REVIEW = 'APP_STORE_REVIEW',
}

/**
 * Types of sentiment data an analysis can produce.
 */
export enum SentimentDataType {
  SENTIMENT_SCORE = 'SENTIMENT_SCORE',
  SHARE_OF_VOICE = 'SHARE_OF_VOICE',
}

/**
 * The status of a report.
 */
export enum Status {
  NEW = 'NEW',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
}

/**
 * Defines the colors for the different report statuses.
 */
export const statusColors: {
  [key in Status]: 'default' | 'secondary' | 'destructive' | 'success' | 'info';
} = {
  NEW: 'secondary',
  IN_PROGRESS: 'info',
  COMPLETED: 'success',
  FAILED: 'destructive',
};


/**
 * Types of artifacts that can be generated for a sentiment report.
 */
export enum ReportArtifactType {
  BQ_TABLE = 'BQ_TABLE',
  GOOGLE_SHEET = 'GOOGLE_SHEET',
}

/**
 * Represents the sentiment data sets created to produce a report.
 */
export interface SentimentReportDataset {
  reportId?: string;
  source?: SocialMediaSource;
  dataOutput?: SentimentDataType;
  datasetUri?: string;
}

/**
 * Represents a single data point in a sentiment analysis.
 */
export interface SentimentDataPoint {
  date: string;
  positive: number;
  negative: number;
  neutral: number;
}

/**
 * Overall sentiment statistics.
 */
export interface OverallSentiment {
  positive: number;
  negative: number;
  neutral: number;
  average: number;
  itemCount?: number;
}

/**
 * Represents the analysis results for a single source.
 */
export interface SourceAnalysisResult {
  sentimentOverTime?: SentimentDataPoint[];
  overallSentiment?: OverallSentiment;
  justificationBreakdown?: JustificationBreakdown;
  justificationCategories?: JustificationCategoryMetadataItem[];
}

/**
 * Represents a single data point in a share of voice analysis.
 */
export interface ShareOfVoiceDataPoint {
  name: string;
  positive: number;
  neutral: number;
  negative: number;
}

/**
 * Represents the share of voice results for a sentiment analysis.
 */
export interface ShareOfVoiceResult {
  shareOfVoice?: ShareOfVoiceDataPoint[];
  overallSentiment?: {
    positive: number;
    negative: number;
    neutral: number;
    average: number;
    itemCount: number;
  };
  justificationBreakdown?: JustificationBreakdown;
  justificationCategories?: JustificationCategoryMetadataItem[];
}

/**
 * Represents a single item in a justification breakdown.
 */
export interface JustificationItem {
  category: string;
  count: number;
}

/**
 * Represents metadata for a justification category, providing a clear
 * definition and a representative example.
 */
export interface JustificationCategoryMetadataItem {
  /** The unique name of the category. */
  categoryName: string;
  /** A concise definition explaining what the category represents. */
  definition: string;
  /** A representative example from the data illustrating the category. */
  representativeExample: string;
}

/**
 * Represents the breakdown of justifications for a sentiment analysis.
 */
export interface JustificationBreakdown {
  positive: JustificationItem[];
  negative: JustificationItem[];
  neutral: JustificationItem[];
}

/**
 * Represents the analysis results for a single source.
 */
export type AnalysisResult =
  | SourceAnalysisResult
  | ShareOfVoiceResult
  | JustificationBreakdown;

/**
 * A report.
 */
export interface SentimentReport {
  reportId?: string;
  createdOn?: string; // ISO string
  lastUpdatedOn?: string; // ISO string
  status?: Status;
  sources: SocialMediaSource[];
  dataOutput: SentimentDataType;
  startTime?: string; // ISO string
  endTime?: string; // ISO string
  includeJustifications?: boolean;
  topic?: string;
  datasets?: SentimentReportDataset[];
  reportArtifactType: ReportArtifactType;
  reportArtifactUri?: string;
  analysisResults?: Partial<Record<SocialMediaSource, AnalysisResult>>;
}

/**
 * Represents a summarized version of a report for list views, omitting datasets.
 */
export type ReportForList = Omit<SentimentReport, 'datasets'>;
