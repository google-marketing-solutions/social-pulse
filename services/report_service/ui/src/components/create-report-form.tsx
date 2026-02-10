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

import {useForm} from 'react-hook-form';
import {zodResolver} from '@hookform/resolvers/zod';
import {z} from 'zod';
import {useEffect, useState, useTransition} from 'react';
import {useRouter} from 'next/navigation';

import {createReport} from '@/lib/actions';
import {createReportSchema} from '@/lib/schema';
import {availableSources} from '@/lib/sources';
import {useToast} from '@/hooks/use-toast';
import {Button} from '@/components/ui/button';
import {Card, CardContent, CardFooter} from '@/components/ui/card';
import {Checkbox} from '@/components/ui/checkbox';
import {DatePicker} from '@/components/ui/date-picker';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {Input} from '@/components/ui/input';
import {Label} from '@/components/ui/label';
import {RadioGroup, RadioGroupItem} from '@/components/ui/radio-group';
import {SentimentDataType, SocialMediaSource} from '@/lib/types';

type FormValues = z.infer<typeof createReportSchema>;

type CreateReportState = {
  success: boolean;
  message: string;
  errors?: {[key: string]: string[]};
};

const initialState: CreateReportState = {
  errors: {},
  message: '',
  success: false,
};

const topicDescriptions = {
  [SentimentDataType.SENTIMENT_SCORE]:
    'The brand, product, or feature to analyze. Ie, "Acme", or "Acme Portable Holes", or "Acme Portable Holes with AI text-to-hole".',
  [SentimentDataType.SHARE_OF_VOICE]:
    'The product category or topic to analyze. I.e., "portable holes", or "best products to capture a road runner."',
};

/**
 * Renders a form to create a new report.
 * @return The create report form component.
 */
export function CreateReportForm() {
  const {toast} = useToast();
  const router = useRouter();
  const [state, setState] = useState(initialState);
  const [isPending, startTransition] = useTransition();

  const form = useForm<FormValues>({
    resolver: zodResolver(createReportSchema),
    defaultValues: {
      topic: '',
      sources: [SocialMediaSource.YOUTUBE_VIDEO],
      dataOutput: SentimentDataType.SENTIMENT_SCORE,
      dateRange: {
        from: new Date(new Date().setDate(new Date().getDate() - 7)),
        to: new Date(),
      },
    },
  });

  useEffect(() => {
    if (state.success) {
      toast({
        title: 'Report submitted!',
        description: 'Your new analysis is being generated.',
      });
      router.push('/');
    } else if (state.message) {
      if (state.errors) {
        Object.entries(state.errors).forEach(([field, errors]) => {
          form.setError(field as keyof FormValues, {
            type: 'manual',
            message: (errors as string[]).join(', '),
          });
        });
      }
      toast({
        variant: 'destructive',
        title: 'Error submitting form',
        description: state.message,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state, toast, router]);

  const onFormSubmit = (data: FormValues) => {
    startTransition(async () => {
      const result = await createReport({}, data);
      setState(result);
    });
  };

  const dataOutput = form.watch('dataOutput');

  return (
    <Card>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onFormSubmit)}>
          <CardContent className="p-6 space-y-6">
            <FormField
              control={form.control}
              name="dataOutput"
              render={({field}) => (
                <FormItem className="space-y-2">
                  <FormLabel>Analysis Type</FormLabel>
                  <FormControl>
                    <RadioGroup
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                      className="flex flex-col space-y-2 pt-1"
                    >
                      <FormItem className="flex items-center space-x-3 space-y-0">
                        <FormControl>
                          <RadioGroupItem
                            value={SentimentDataType.SENTIMENT_SCORE}
                          />
                        </FormControl>
                        <FormLabel className="font-normal cursor-pointer">
                          Sentiment Analysis
                        </FormLabel>
                      </FormItem>
                      <FormItem className="flex items-center space-x-3 space-y-0">
                        <FormControl>
                          <RadioGroupItem
                            value={SentimentDataType.SHARE_OF_VOICE}
                          />
                        </FormControl>
                        <FormLabel className="font-normal cursor-pointer">
                          Share of Voice
                        </FormLabel>
                      </FormItem>
                    </RadioGroup>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="topic"
              render={({field}) => (
                <FormItem>
                  <FormLabel>Topic</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="e.g., 'Next.js 15' or 'My Brand'"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    {topicDescriptions[dataOutput]}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex flex-col sm:flex-row gap-4">
              <FormField
                control={form.control}
                name="dateRange.from"
                render={({field}) => (
                  <FormItem className="flex flex-col">
                    <FormLabel>Start Date</FormLabel>
                    <FormControl>
                      <DatePicker
                        date={field.value}
                        onDateChange={field.onChange}
                        placeholder="Pick a start date"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="dateRange.to"
                render={({field}) => (
                  <FormItem className="flex flex-col">
                    <FormLabel>End Date</FormLabel>
                    <FormControl>
                      <DatePicker
                        date={field.value}
                        onDateChange={field.onChange}
                        placeholder="Pick an end date"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="sources"
              render={() => (
                <FormItem>
                  <FormLabel>Sources</FormLabel>
                  <div className="space-y-2 pt-2">
                    {availableSources.map(source => (
                      <FormField
                        key={source.id}
                        control={form.control}
                        name="sources"
                        render={({field}) => {
                          return (
                            <FormItem
                              key={source.id}
                              className="flex flex-row items-start space-x-3 space-y-0"
                            >
                              <FormControl>
                                <Checkbox
                                  id={source.id}
                                  checked={field.value?.includes(source.id)}
                                  onCheckedChange={checked => {
                                    return checked
                                      ? field.onChange([
                                          ...field.value,
                                          source.id,
                                        ])
                                      : field.onChange(
                                          field.value?.filter(
                                            value => value !== source.id,
                                          ),
                                        );
                                  }}
                                />
                              </FormControl>
                              <Label
                                htmlFor={source.id}
                                className="font-normal flex items-center gap-2 cursor-pointer"
                              >
                                {source.icon} {source.label}
                              </Label>
                            </FormItem>
                          );
                        }}
                      />
                    ))}
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
          <CardFooter>
            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending ? 'Creating...' : 'Create Report'}
            </Button>
          </CardFooter>
        </form>
      </Form>
    </Card>
  );
}
