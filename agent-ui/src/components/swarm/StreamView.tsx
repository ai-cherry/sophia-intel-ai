'use client';

import { useState, useEffect } from 'react';
import { usePlaygroundStore } from '@/store';
import { StreamResponse } from '@/types/swarm';
import { JudgeReport } from './JudgeReport';
import { ToolCalls } from './ToolCalls';
import { Citations } from './Citations';
import { CriticReport } from './CriticReport';
import { cn } from '@/lib/utils';

interface StreamViewProps {
  streamContent?: string;
  lastResponse?: StreamResponse | null;
  isStreaming?: boolean;
}

export function StreamView({ 
  streamContent: externalStreamContent, 
  lastResponse: externalLastResponse, 
  isStreaming: externalIsStreaming 
}: StreamViewProps = {}) {
  // Use external props if provided, otherwise fall back to store
  const { isStreaming: storeIsStreaming } = usePlaygroundStore();
  
  // For this component, we'll primarily rely on props passed from parent components
  // since the streaming state is managed in TeamWorkflowPanel
  const streamContent = externalStreamContent || '';
  const lastResponse = externalLastResponse || null;
  const isStreaming = externalIsStreaming ?? storeIsStreaming;

  if (!streamContent && !lastResponse) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500 border">
        <div className="flex flex-col items-center gap-2">
          <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center">
            <span className="text-gray-400">⚡</span>
          </div>
          <p className="text-sm">No output yet. Run a team or workflow to see results.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 space-y-6 border">
      {/* Stream Content */}
      {streamContent && (
        <div className="prose max-w-none">
          <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
            <span>Output</span>
            {isStreaming && (
              <span className="text-sm text-blue-600 bg-blue-50 px-2 py-1 rounded-full flex items-center gap-1">
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                Streaming
              </span>
            )}
          </h3>
          <div className="bg-gray-50 rounded-md p-4 font-mono text-sm whitespace-pre-wrap border">
            {streamContent}
            {isStreaming && (
              <span className="inline-block w-2 h-4 bg-blue-600 animate-pulse ml-1" />
            )}
          </div>
        </div>
      )}

      {/* Structured Results */}
      {lastResponse && (
        <div className="space-y-6">
          {/* Critic Review */}
          {lastResponse.critic && (
            <div className="border-t pt-6">
              <CriticReport data={lastResponse.critic} />
            </div>
          )}

          {/* Judge Decision */}
          {lastResponse.judge && (
            <div className="border-t pt-6">
              <JudgeReport data={lastResponse.judge} />
            </div>
          )}

          {/* Tool Calls */}
          {lastResponse.tool_calls && lastResponse.tool_calls.length > 0 && (
            <div className="border-t pt-6">
              <ToolCalls calls={lastResponse.tool_calls} />
            </div>
          )}

          {/* Citations */}
          {lastResponse.citations && lastResponse.citations.length > 0 && (
            <div className="border-t pt-6">
              <Citations items={lastResponse.citations} />
            </div>
          )}
        </div>
      )}

      {/* Summary Footer */}
      {(streamContent || lastResponse) && (
        <div className="border-t pt-4 text-xs text-gray-500 flex justify-between items-center">
          <span>
            {streamContent && `${streamContent.length} characters streamed`}
            {streamContent && lastResponse && ' • '}
            {lastResponse && `${Object.keys(lastResponse).length} structured sections`}
          </span>
          {isStreaming && (
            <span className="text-blue-600">Processing...</span>
          )}
        </div>
      )}
    </div>
  );
}