'use client';

import { useState } from 'react';
import { Citation } from '@/lib/types';

interface CitationsProps {
  items?: Citation[];
}

export function Citations({ items = [] }: CitationsProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  if (!items.length) return null;

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
      <h3 className="text-lg font-semibold mb-2">Citations</h3>
      <div className="space-y-2">
        {items.map((citation, i) => {
          const location = `${citation.path || 'unknown'}:${
            citation.start_line || 0
          }-${citation.end_line || 0}`;

          return (
            <div
              key={i}
              className="border rounded-md p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => toggleExpanded(i)}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">[{i + 1}]</span>
                  <code className="text-sm font-mono text-blue-600">
                    {location}
                  </code>
                  {citation.lang && (
                    <span className="text-xs px-2 py-0.5 bg-gray-200 rounded">
                      {citation.lang}
                    </span>
                  )}
                </div>
                <svg
                  className={`w-4 h-4 text-gray-500 transition-transform ${
                    expanded.has(i) ? 'rotate-90' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </div>

              {expanded.has(i) && citation.content && (
                <div className="mt-3 pt-3 border-t">
                  <pre className="text-xs bg-white p-3 rounded overflow-x-auto font-mono">
                    <code className={`language-${citation.lang || 'text'}`}>
                      {citation.content}
                    </code>
                  </pre>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}