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

import Link from 'next/link';
import Image from 'next/image';
import {PlusCircle} from 'lucide-react';
import {Button} from '@/components/ui/button';
import {PlaceHolderImages} from '@/lib/placeholder-images';

/**
 * The header for the application.
 * @return The header component.
 */
export function Header() {
  const logo = PlaceHolderImages.find(img => img.id === 'logo');

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur">
      <div className="container flex h-14 items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-bold">
          {logo && (
            <Image
              src={logo.imageUrl}
              alt={logo.description}
              data-ai-hint={logo.imageHint}
              width={28}
              height={28}
            />
          )}
          <span className="font-headline text-lg">Social Pulse</span>
        </Link>
        <nav>
          <Button asChild variant="ghost">
            <Link href="/create">
              <PlusCircle className="mr-2 h-4 w-4" />
              New Analysis
            </Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}
