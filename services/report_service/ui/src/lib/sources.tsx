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
