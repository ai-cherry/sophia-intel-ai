'use client';

import { useUIStore } from '@/state/ui';
import { JudgeReport } from './JudgeReport';
import { ToolCalls } from './ToolCalls';
import { Citations } from './Citations';
import { CriticReport } from './CriticReport';

export function StreamView() {
  const { streamContent, lastResponse, isStreaming } = useUIStore();

  if (!streamContent && !lastResponse) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
        <p>No output yet. Run a team or workflow to see results.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 space-y-6">
      {/* Stream Content */}
      {streamContent && (
        <div className="prose max-w-none">
          <h3 className="text-lg font-semibold mb-2">Output</h3>
          <div className="bg-gray-50 rounded-md p-4 font-mono text-sm whitespace-pre-wrap">
            {streamContent}
            {isStreaming && <span className="inline-block w-2 h-4 bg-blue-600 animate-pulse ml-1" />}
          </div>
        </div>
      )}

      {/* Structured Results */}
      {lastResponse && (
        <>
          {/* Critic Review */}
          {lastResponse.critic && (
            <CriticReport data={lastResponse.critic} />
          )}

          {/* Judge Decision */}
          {lastResponse.judge && (
            <JudgeReport data={lastResponse.judge} />
          )}

          {/* Tool Calls */}
          {lastResponse.tool_calls && lastResponse.tool_calls.length > 0 && (
            <ToolCalls calls={lastResponse.tool_calls} />
          )}

          {/* Citations */}
          {lastResponse.citations && lastResponse.citations.length > 0 && (
            <Citations items={lastResponse.citations} />
          )}
        </>
      )}
    </div>
  );
}