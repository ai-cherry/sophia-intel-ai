'use client';

import { useState } from 'react';
import { CriticReview } from '@/types/swarm';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface CriticReportProps {
  data: CriticReview | string | Record<string, unknown>;
}

export function CriticReport({ data }: CriticReportProps) {
  const [collapsed, setCollapsed] = useState(false);
  
  if (!data) return null;

  const critic = typeof data === 'string' ? safe(data) : data;
  const isPassing = critic.verdict === 'pass';

  return (
    <div className="prose max-w-none">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold">Critic Review</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
          className="text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50"
        >
          {collapsed ? 'Expand' : 'Collapse'}
        </Button>
      </div>

      {/* Verdict Banner */}
      <div
        className={cn(
          'p-3 rounded-md mb-3',
          isPassing
            ? 'bg-green-50 border border-green-200'
            : 'bg-yellow-50 border border-yellow-200'
        )}
      >
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'text-xl',
              isPassing ? 'text-green-600' : 'text-yellow-600'
            )}
          >
            {isPassing ? '✓' : '⚠'}
          </span>
          <span
            className={cn(
              'font-semibold',
              isPassing ? 'text-green-700' : 'text-yellow-700'
            )}
          >
            Verdict: {critic.verdict?.toUpperCase()}
          </span>
        </div>
      </div>

      {!collapsed && (
        <div className="space-y-3">
          {/* Must Fix */}
          {critic.must_fix && critic.must_fix.length > 0 && (
            <div>
              <h4 className="font-medium text-red-700 mb-1">Must Fix:</h4>
              <ul className="list-disc list-inside space-y-1">
                {critic.must_fix.map((item: string, i: number) => (
                  <li key={i} className="text-sm text-red-600">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Findings */}
          {critic.findings && (
            <div className="space-y-2">
              <h4 className="font-medium text-gray-700">Findings:</h4>
              {Object.entries(critic.findings).map(([category, issues]) => {
                if (!Array.isArray(issues) || issues.length === 0) return null;
                return (
                  <div key={category} className="ml-2">
                    <h5 className="text-sm font-medium text-gray-600 capitalize">
                      {category.replace(/_/g, ' ')}:
                    </h5>
                    <ul className="list-disc list-inside ml-2">
                      {issues.map((issue: string, i: number) => (
                        <li key={i} className="text-sm text-gray-600">
                          {issue}
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          )}

          {/* Nice to Have */}
          {critic.nice_to_have && critic.nice_to_have.length > 0 && (
            <div>
              <h4 className="font-medium text-blue-700 mb-1">Nice to Have:</h4>
              <ul className="list-disc list-inside space-y-1">
                {critic.nice_to_have.map((item: string, i: number) => (
                  <li key={i} className="text-sm text-blue-600">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Patch Notes */}
          {critic.minimal_patch_notes && (
            <div>
              <h4 className="font-medium text-gray-700 mb-1">Patch Notes:</h4>
              <p className="text-sm text-gray-600">{critic.minimal_patch_notes}</p>
            </div>
          )}

          {/* Full JSON */}
          <details className="mt-4">
            <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
              View Full JSON
            </summary>
            <pre className="mt-2 text-xs bg-gray-50 p-3 rounded overflow-x-auto">
              {JSON.stringify(critic, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}

function safe(s: string): CriticReview | null {
  try {
    return JSON.parse(s);
  } catch {
    return {};
  }
}