'use client';

import { useState } from 'react';
import { JudgeDecision } from '@/types/swarm';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface JudgeReportProps {
  data: JudgeDecision | string | any;
}

const allowed = (j: any): boolean => {
  return (
    j &&
    ['accept', 'merge'].includes(j.decision) &&
    Array.isArray(j.runner_instructions) &&
    j.runner_instructions.length > 0
  );
};

export function JudgeReport({ data }: JudgeReportProps) {
  const [collapsed, setCollapsed] = useState(false);

  if (!data) return null;

  const judge = typeof data === 'string' ? safe(data) : data;
  const isAllowed = allowed(judge);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(JSON.stringify(judge, null, 2));
  };

  return (
    <div className="prose max-w-none">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold">Judge Decision</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
          className="text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50"
        >
          {collapsed ? 'Expand' : 'Collapse'}
        </Button>
      </div>

      {/* Runner Gate Banner */}
      <div
        className={cn(
          'p-4 rounded-md mb-4',
          isAllowed
            ? 'bg-green-50 border border-green-200'
            : 'bg-red-50 border border-red-200'
        )}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                'text-2xl',
                isAllowed ? 'text-green-600' : 'text-red-600'
              )}
            >
              {isAllowed ? '✓' : '✗'}
            </span>
            <div>
              <div
                className={cn(
                  'font-semibold',
                  isAllowed ? 'text-green-700' : 'text-red-700'
                )}
              >
                Runner Gate: {isAllowed ? 'ALLOWED' : 'BLOCKED'}
              </div>
              {judge.decision && (
                <div className="text-sm text-gray-600">
                  Decision: <span className="font-mono">{judge.decision}</span>
                </div>
              )}
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={copyToClipboard}
            className="text-sm"
          >
            Copy JSON
          </Button>
        </div>
      </div>

      {/* Details */}
      {!collapsed && (
        <div className="space-y-3">
          {/* Runner Instructions */}
          {judge.runner_instructions && judge.runner_instructions.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-700 mb-1">
                Runner Instructions:
              </h4>
              <ul className="list-disc list-inside space-y-1">
                {judge.runner_instructions.map((instruction: string, i: number) => (
                  <li key={i} className="text-sm text-gray-600">
                    {instruction}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Rationale */}
          {judge.rationale && judge.rationale.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-700 mb-1">Rationale:</h4>
              <ul className="list-disc list-inside space-y-1">
                {judge.rationale.map((reason: string, i: number) => (
                  <li key={i} className="text-sm text-gray-600">
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Selected Proposal */}
          {judge.selected && (
            <div>
              <h4 className="font-medium text-gray-700 mb-1">
                Selected Proposal:
              </h4>
              <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                {judge.selected}
              </span>
            </div>
          )}

          {/* Full JSON */}
          <details className="mt-4">
            <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
              View Full JSON
            </summary>
            <pre className="mt-2 text-xs bg-gray-50 p-3 rounded overflow-x-auto">
              {JSON.stringify(judge, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}

function safe(s: string): any {
  try {
    return JSON.parse(s);
  } catch {
    return {};
  }
}
