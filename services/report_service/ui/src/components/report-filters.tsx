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

import * as React from 'react';
import {useRouter, usePathname, useSearchParams} from 'next/navigation';
import {Check, X, Filter} from 'lucide-react';

import {cn} from '@/lib/utils';
import {Button} from '@/components/ui/button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import {DatePicker} from '@/components/ui/date-picker';
import {getReportChannels} from '@/lib/actions';

interface ReportFiltersProps {
  /** The ID of the report to filter. */
  reportId?: string;
  /** The channels to exclude from the report. */
  excludedChannels?: string[];
  /** The default start date for the report. */
  defaultStartDate?: string;
  /** The default end date for the report. */
  defaultEndDate?: string;
}

const DEFAULT_EXCLUDED: string[] = [];

/**
 * Renders a dialog for filtering reports.
 *
 * @return The report filters component.
 */
export function ReportFilters({
  reportId,
  excludedChannels = DEFAULT_EXCLUDED,
  defaultStartDate,
  defaultEndDate,
}: ReportFiltersProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [startDate, setStartDate] = React.useState<Date | undefined>(
    searchParams.get('startDate')
      ? new Date(searchParams.get('startDate')!)
      : defaultStartDate
        ? new Date(defaultStartDate)
        : undefined,
  );
  const [endDate, setEndDate] = React.useState<Date | undefined>(
    searchParams.get('endDate')
      ? new Date(searchParams.get('endDate')!)
      : defaultEndDate
        ? new Date(defaultEndDate)
        : undefined,
  );

  const [open, setOpen] = React.useState(false);
  const [channels, setChannels] = React.useState<string[]>([]);
  const [loadingChannels, setLoadingChannels] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState('');

  // Local state for the dialog before applying
  const [tempExcluded, setTempExcluded] = React.useState<Set<string>>(
    new Set(excludedChannels),
  );

  // Sync temp state when props change (e.g. navigation)
  React.useEffect(() => {
    setTempExcluded(prev => {
      const isSame =
        prev.size === excludedChannels.length &&
        excludedChannels.every(c => prev.has(c));
      return isSame ? prev : new Set(excludedChannels);
    });
  }, [excludedChannels]);

  // Fetch all channels on mount
  React.useEffect(() => {
    if (!reportId) return;

    setLoadingChannels(true);
    getReportChannels(reportId)
      .then(data => {
        setChannels(data);
      })
      .catch(err => console.error('Failed to load channels', err))
      .finally(() => setLoadingChannels(false));
  }, [reportId]);

  const handleSelectAll = (e: React.MouseEvent) => {
    e.preventDefault();
    setTempExcluded(new Set());
  };

  const handleClearAll = (e: React.MouseEvent) => {
    e.preventDefault();
    setTempExcluded(new Set(channels));
  };

  // ... (rest of logic) ...

  // Sync with URL
  const updateFilters = React.useCallback(
    (
      newExcluded: string[],
      newStart: Date | undefined,
      newEnd: Date | undefined,
    ) => {
      const params = new URLSearchParams();
      // Preserve existing params except ours AND channelTitle (legacy inclusion)
      searchParams.forEach((value, key) => {
        if (
          ![
            'excludedChannels',
            'startDate',
            'endDate',
            'channelTitle',
          ].includes(key)
        ) {
          params.append(key, value);
        }
      });

      newExcluded.forEach(c => params.append('excludedChannels', c));

      if (newStart) {
        params.set('startDate', newStart.toISOString());
      }

      if (newEnd) {
        params.set('endDate', newEnd.toISOString());
      }

      router.push(`${pathname}?${params.toString()}`);
    },
    [router, pathname, searchParams],
  );

  const handleApplyChannels = () => {
    setOpen(false);
    updateFilters(Array.from(tempExcluded), startDate, endDate);
  };

  const toggleChannelExclusion = (channel: string) => {
    const newExcluded = new Set(tempExcluded);
    if (newExcluded.has(channel)) {
      newExcluded.delete(channel);
    } else {
      newExcluded.add(channel);
    }
    setTempExcluded(newExcluded);
  };

  const handleStartDateChange = (date: Date | undefined) => {
    setStartDate(date);
    updateFilters(Array.from(tempExcluded), date, endDate);
  };

  const handleEndDateChange = (date: Date | undefined) => {
    setEndDate(date);
    updateFilters(Array.from(tempExcluded), startDate, date);
  };

  const clearFilters = () => {
    setTempExcluded(new Set());
    setStartDate(undefined);
    setEndDate(undefined);
    router.push(pathname);
  };

  return (
    <div className="mb-6 space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Channel Filter (Left Side) - Now Exclusion based */}
        <div className="flex-1 flex flex-wrap items-center gap-2">
          <Dialog
            open={open}
            onOpenChange={isOpen => {
              if (isOpen) {
                setTempExcluded(new Set(excludedChannels));
              }
              setOpen(isOpen);
            }}
          >
            <DialogTrigger asChild>
              <Button
                variant="outline"
                className="w-auto min-w-[200px] justify-between"
              >
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4" />
                  <span>
                    {excludedChannels.length > 0 && channels.length > 0
                      ? `${channels.length - excludedChannels.length} channels selected`
                      : 'Filter channels...'}
                  </span>
                </div>
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px] max-h-[85vh] flex flex-col">
              <DialogHeader>
                <DialogTitle>Filter Channels</DialogTitle>
                <DialogDescription>
                  Select which channels to include in the report analysis.
                </DialogDescription>
              </DialogHeader>
              <div className="flex justify-between items-center text-sm py-2 px-1">
                <div>
                  <button onClick={handleSelectAll} className="text-blue-600 hover:text-blue-800 hover:underline">Select all {channels.length}</button>
                  <span className="mx-2 text-muted-foreground">-</span>
                  <button onClick={handleClearAll} className="text-blue-600 hover:text-blue-800 hover:underline">Clear</button>
                </div>
                <div className="text-muted-foreground">
                  Displaying {channels.length}
                </div>
              </div>
              <div className="flex-1 min-h-0 overflow-hidden">
                <Command
                  className="h-full border rounded-md"
                >
                  <CommandInput
                    placeholder="Search channel..."
                    value={searchQuery}
                    onValueChange={setSearchQuery}
                  />
                  <CommandList className="h-full overflow-y-auto">
                    {loadingChannels ? (
                      <div className="py-6 text-center text-sm text-muted-foreground">
                        Loading...
                      </div>
                    ) : (
                      <>
                        <CommandEmpty>No channel found.</CommandEmpty>
                        <CommandGroup>
                          {channels.map(channel => {
                            const isIncluded = !tempExcluded.has(channel);
                            return (
                              <CommandItem
                                key={channel}
                                value={channel}
                                onSelect={() => toggleChannelExclusion(channel)}
                                className="cursor-pointer"
                              >
                                <div
                                  className={cn(
                                    'mr-2 flex h-4 w-4 items-center justify-center',
                                    isIncluded
                                      ? 'text-primary'
                                      : 'opacity-0'
                                  )}
                                >
                                  <Check className="h-4 w-4" />
                                </div>
                                <span>{channel}</span>
                              </CommandItem>
                            );
                          })}
                        </CommandGroup>
                      </>
                    )}
                  </CommandList>
                </Command>
              </div>
              <DialogFooter>
                <Button
                  variant="secondary"
                  onClick={() => setTempExcluded(new Set())}
                >
                  Reset Selection
                </Button>
                <Button onClick={handleApplyChannels}>Apply Filter</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Date Range Filters (Right Side) */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="flex items-center gap-2">
            <DatePicker
              date={startDate}
              onDateChange={handleStartDateChange}
              placeholder="Start Date"
            />
            <span className="text-muted-foreground">-</span>
            <DatePicker
              date={endDate}
              onDateChange={handleEndDateChange}
              placeholder="End Date"
            />
          </div>

          {(excludedChannels.length > 0 || startDate || endDate) && (
            <Button
              variant="ghost"
              onClick={clearFilters}
              className="h-8 px-2 lg:px-3"
            >
              Reset
              <X className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
