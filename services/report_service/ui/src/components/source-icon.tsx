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
