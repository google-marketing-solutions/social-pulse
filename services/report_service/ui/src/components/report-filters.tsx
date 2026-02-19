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
import {Badge} from '@/components/ui/badge';

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

  // Debounced search for channels
  React.useEffect(() => {
    if (!open || !reportId) return;

    const timer = setTimeout(() => {
      if (searchQuery.length > 0) {
        setLoadingChannels(true);
        getReportChannels(reportId, searchQuery)
          .then(data => {
            setChannels(data);
          })
          .catch(err => console.error('Failed to load channels', err))
          .finally(() => setLoadingChannels(false));
      } else {
        setChannels([]);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [reportId, searchQuery, open]);

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
                    {excludedChannels.length > 0
                      ? `${excludedChannels.length} excluded`
                      : 'Select channels to exclude...'}
                  </span>
                </div>
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px] max-h-[85vh] flex flex-col">
              <DialogHeader>
                <DialogTitle>Exclude Channels</DialogTitle>
                <DialogDescription>
                  Search and select channels to exclude from the report
                  analysis.
                </DialogDescription>
              </DialogHeader>
              <div className="flex-1 min-h-0 overflow-hidden">
                <Command
                  className="h-full border rounded-md"
                  shouldFilter={false}
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
                        <CommandEmpty>
                          {searchQuery.length === 0
                            ? 'Start typing to search...'
                            : 'No channel found.'}
                        </CommandEmpty>
                        <CommandGroup heading="Search Results">
                          {channels.map(channel => {
                            const isExcluded = tempExcluded.has(channel);
                            return (
                              <CommandItem
                                key={channel}
                                value={channel}
                                onSelect={() => toggleChannelExclusion(channel)}
                                className="data-[selected='true']:bg-muted data-[selected='true']:text-muted-foreground"
                              >
                                <div
                                  className={cn(
                                    'mr-2 flex h-4 w-4 items-center justify-center rounded-sm border-2 border-primary',
                                    isExcluded
                                      ? 'bg-primary text-primary-foreground'
                                      : 'opacity-50 [&_svg]:invisible',
                                  )}
                                >
                                  <Check className={cn('h-4 w-4')} />
                                </div>
                                <span
                                  className={
                                    isExcluded
                                      ? 'text-muted-foreground line-through decoration-destructive'
                                      : ''
                                  }
                                >
                                  {channel}
                                </span>
                              </CommandItem>
                            );
                          })}
                        </CommandGroup>
                      </>
                    )}
                    {tempExcluded.size > 0 && searchQuery.length === 0 && (
                      <CommandGroup heading="Currently Excluded">
                        {Array.from(tempExcluded).map(channel => (
                          <CommandItem
                            key={channel}
                            value={channel}
                            onSelect={() => toggleChannelExclusion(channel)}
                          >
                            <div className="mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary bg-primary text-primary-foreground">
                              <Check className="h-4 w-4" />
                            </div>
                            <span className="text-muted-foreground line-through decoration-destructive">
                              {channel}
                            </span>
                          </CommandItem>
                        ))}
                      </CommandGroup>
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
          {excludedChannels.length > 0 && (
            <div className="flex flex-wrap gap-1 items-center">
              {excludedChannels.map(c => (
                <Badge
                  variant="destructive"
                  key={c}
                  className="text-xs whitespace-nowrap px-1 flex items-center gap-1"
                >
                  {c}
                  <button
                    onClick={() => {
                      const newExcluded = excludedChannels.filter(e => e !== c);
                      updateFilters(newExcluded, startDate, endDate);
                    }}
                    className="ml-1 hover:bg-destructive-foreground/20 rounded-full p-0.5"
                    type="button"
                  >
                    <X className="h-3 w-3" />
                    <span className="sr-only">Remove {c}</span>
                  </button>
                </Badge>
              ))}
            </div>
          )}
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
