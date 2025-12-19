import {SocialMediaSource} from './types';
import {Video, MessageSquare, Twitter, AppWindow} from 'lucide-react';

/**
 * The type of metric to use for a source.
 */
export type MetricType = 'VIEWS' | 'NUM_PUBLISHED' | 'UPVOTES';

/**
 * The configuration for a social source.
 */
export interface SourceConfig {
  id: SocialMediaSource;
  label: string;
  metric: MetricType;
  metricLabel: string;
  icon: React.ReactNode;
}

/**
 * The configuration for each social source.
 */
export const sourceConfiguration: Record<SocialMediaSource, SourceConfig> = {
  [SocialMediaSource.YOUTUBE_VIDEO]: {
    id: SocialMediaSource.YOUTUBE_VIDEO,
    label: 'YouTube Videos',
    metric: 'VIEWS',
    metricLabel: 'Views',
    icon: <Video className="h-4 w-4" />,
  },
  [SocialMediaSource.YOUTUBE_COMMENT]: {
    id: SocialMediaSource.YOUTUBE_COMMENT,
    label: 'YouTube Comments',
    metric: 'NUM_PUBLISHED',
    metricLabel: 'Comments',
    icon: <MessageSquare className="h-4 w-4" />,
  },
  [SocialMediaSource.REDDIT_POST]: {
    id: SocialMediaSource.REDDIT_POST,
    label: 'Reddit Posts',
    metric: 'UPVOTES',
    metricLabel: 'Upvotes',
    icon: <MessageSquare className="h-4 w-4" />, // Using MessageSquare as a placeholder for Reddit
  },
  [SocialMediaSource.X_POST]: {
    id: SocialMediaSource.X_POST,
    label: 'X Posts',
    metric: 'VIEWS', // Assuming views for X posts
    metricLabel: 'Views',
    icon: <Twitter className="h-4 w-4" />,
  },
  [SocialMediaSource.APP_STORE_REVIEW]: {
    id: SocialMediaSource.APP_STORE_REVIEW,
    label: 'App Store Reviews',
    metric: 'NUM_PUBLISHED', // Assuming number of reviews
    metricLabel: 'Reviews',
    icon: <AppWindow className="h-4 w-4" />,
  },
};

/**
 * A list of available social sources.
 */
export const availableSources = Object.values(sourceConfiguration).filter(
  Boolean,
) as SourceConfig[];
