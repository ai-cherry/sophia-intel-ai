'use client';

import { useState } from 'react';
import { ToolCall } from '@/types/swarm';
import { cn } from '@/lib/utils';
import Icon from '@/components/ui/icon';

interface ToolCallsProps {
  calls?: ToolCall[];
}

export function ToolCalls({ calls = [] }: ToolCallsProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  if (!Array.isArray(calls) || !calls.length) return null;

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expanded);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpanded(newExpanded);
  };

  return (
    <div className="prose max-w-none">
      <h3 className="text-lg font-semibold mb-2">Tool Calls</h3>
      <div className="space-y-2">
        {calls.map((call, i) => (
          <div
            key={i}
            className="border rounded-md p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <div
              className="flex items-center justify-between cursor-pointer"
              onClick={() => toggleExpanded(i)}
            >
              <div className="flex items-center gap-2">
                <span className="text-blue-600 font-mono font-medium">
                  {call.name}
                </span>
                {call.args && Object.keys(call.args).length > 0 && (
                  <span className="text-xs text-gray-500">
                    ({Object.keys(call.args).length} args)
                  </span>
                )}
              </div>
              <Icon
                type="chevron-down"
                size="xs"
                className={cn(
                  'text-gray-500 transition-transform',
                  expanded.has(i) ? '' : '-rotate-90'
                )}
              />
            </div>
            
            {expanded.has(i) && call.args && (
              <div className="mt-2 pt-2 border-t">
                <pre className="text-xs bg-white p-2 rounded overflow-x-auto">
                  {JSON.stringify(call.args, null, 2)}
                </pre>
              </div>
            )}
            
            {expanded.has(i) && call.result && (
              <div className="mt-2">
                <div className="text-xs text-gray-600 mb-1">Result:</div>
                <pre className="text-xs bg-white p-2 rounded overflow-x-auto">
                  {typeof call.result === 'string'
                    ? call.result
                    : JSON.stringify(call.result, null, 2)}
                </pre>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}