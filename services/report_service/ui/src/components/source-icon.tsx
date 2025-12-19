'use client';

import {SocialMediaSource} from '@/lib/types';
import {sourceConfiguration} from '@/lib/sources';

export function SourceIcon({source}: {source: SocialMediaSource}) {
  const config = sourceConfiguration[source];
  if (config && config.icon) {
    return config.icon;
  }
  return null;
}
