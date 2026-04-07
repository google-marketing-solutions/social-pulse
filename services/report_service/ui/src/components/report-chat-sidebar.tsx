// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

'use client';

import {useState, useRef, useEffect} from 'react';
import {MessageCircle, Send, User, Bot, Loader2} from 'lucide-react';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {ScrollArea} from '@/components/ui/scroll-area';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import {chatAboutReport} from '@/lib/actions';
import {ChatMessage} from '@/lib/types';
import ReactMarkdown from 'react-markdown';

/**
 * Renders the chat sidebar for a report, displaying AI-generated
 * responses to user queries about the report. This component is useful for
 * giving users a quick way to explore the data in their report.
 */
// TODO(jcryan): Add UI testing for this component.
export function ReportChatSidebar({reportId}: {reportId: string}) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({behavior: 'smooth'});
    }
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput('');
    const newMessages = [...messages, {role: 'user', content: userMsg}];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const response = await chatAboutReport(reportId, {
        query: userMsg,
        history: messages,
      });

      setMessages([
        ...newMessages,
        {role: 'model', content: response.response},
      ]);
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages([
        ...newMessages,
        {
          role: 'model',
          content:
            'Sorry, I encountered an error while trying to respond. Please try again later.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg hover:shadow-xl transition-all z-40 bg-blue-600 hover:bg-blue-700"
        size="icon"
      >
        <MessageCircle className="h-6 w-6" />
      </Button>

      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetContent className="w-full sm:max-w-md md:w-[450px] flex flex-col p-0 border-l border-slate-200">
          <SheetHeader className="p-4 border-b border-slate-100 bg-slate-50 relative pb-4">
            <SheetTitle className="flex items-center gap-2 font-headline text-lg">
              <Bot className="h-5 w-5 text-blue-600" />
              Report Assistant
            </SheetTitle>
            <SheetDescription className="sr-only">
              Chat interface to ask questions about the report data.
            </SheetDescription>
          </SheetHeader>

          <ScrollArea className="flex-1 p-4 bg-slate-50/50">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-4 text-slate-500 mt-12">
                <div className="bg-slate-100 p-4 rounded-full">
                  <MessageCircle className="h-8 w-8 text-slate-400" />
                </div>
                <div>
                  <p className="font-medium text-slate-700">
                    Ask me about this report
                  </p>
                  <p className="text-sm mt-1 max-w-[250px]">
                    I can help you explore specific metrics, track trends, or
                    analyze anomalies in the data.
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-4 pb-4">
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex items-start gap-3 ${
                      msg.role === 'user' ? 'flex-row-reverse' : ''
                    }`}
                  >
                    <div
                      className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center border shadow-sm ${
                        msg.role === 'user'
                          ? 'bg-slate-900 border-slate-900 text-white'
                          : 'bg-white border-blue-200 text-blue-600'
                      }`}
                    >
                      {msg.role === 'user' ? (
                        <User className="h-4 w-4" />
                      ) : (
                        <Bot className="h-4 w-4" />
                      )}
                    </div>
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                        msg.role === 'user'
                          ? 'bg-slate-900 text-slate-50 rounded-br-none'
                          : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none prose prose-sm prose-slate max-w-none'
                      }`}
                    >
                      {msg.role === 'user' ? (
                        msg.content
                      ) : (
                        <div className="markdown-body">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center border shadow-sm bg-white border-blue-200 text-blue-600">
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                    <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none px-4 py-3 text-sm shadow-sm flex items-center gap-1">
                      <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                      <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                      <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
                    </div>
                  </div>
                )}
                <div ref={scrollRef} />
              </div>
            )}
          </ScrollArea>

          <div className="p-4 bg-white border-t border-slate-100 shadow-[0_-10px_20px_-10px_rgba(0,0,0,0.05)]">
            <div className="relative flex items-center">
              <Input
                placeholder="Ask about the data..."
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="pr-12 py-6 rounded-full bg-slate-50 border-slate-200 focus-visible:ring-blue-500 shadow-inner"
              />
              <Button
                size="icon"
                disabled={!input.trim() || isLoading}
                onClick={handleSend}
                className="absolute right-1.5 h-9 w-9 rounded-full bg-blue-600 hover:bg-blue-700 transition-colors"
              >
                <Send className="h-4 w-4 ml-0.5" />
                <span className="sr-only">Send</span>
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
