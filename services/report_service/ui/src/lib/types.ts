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
  COLLECTING_DATA = 'COLLECTING_DATA',
  DATA_COLLECTED = 'DATA_COLLECTED',
  GENERATING_REPORT = 'GENERATING_REPORT',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
}

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

export interface SentimentDataPoint {
  date: string;
  positive: number;
  negative: number;
  neutral: number;
}

export interface SourceAnalysisResult {
  sentimentOverTime?: SentimentDataPoint[];
  overallSentiment?: {
    positive: number;
    negative: number;
    neutral: number;
    average: number;
  };
}

export interface ShareOfVoiceDataPoint {
  name: string;
  positive: number;
  neutral: number;
  negative: number;
}

export interface ShareOfVoiceResult {
  shareOfVoice?: ShareOfVoiceDataPoint[];
}

export type AnalysisResult = SourceAnalysisResult | ShareOfVoiceResult;

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

export type ReportForList = Omit<SentimentReport, 'datasets'>;
