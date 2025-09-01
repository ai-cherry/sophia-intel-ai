'use client';

import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface OutputPhase {
  phase: string;
  token: string;
  critic?: any;
  judge?: any;
  gates?: any;
  final?: any;
}

interface EnhancedOutputProps {
  streamData?: string;
}

export function EnhancedOutput({ streamData = '' }: EnhancedOutputProps) {
  const [phases, setPhases] = useState<OutputPhase[]>([]);
  const [finalResult, setFinalResult] = useState<any>(null);

  useEffect(() => {
    if (!streamData) return;

    // Parse the streaming data - simplified for Phase 1
    const lines = streamData.split('\n');
    const parsedPhases: OutputPhase[] = [];
    
    lines.forEach(line => {
      if (line.startsWith('data: ') && !line.includes('[DONE]')) {
        try {
          const data = JSON.parse(line.substring(6));
          parsedPhases.push(data);
          
          if (data.phase === 'complete' && data.final) {
            setFinalResult(data.final);
          }
        } catch (e) {
          // Skip malformed lines
        }
      }
    });

    setPhases(parsedPhases);
  }, [streamData]);

  const getPhaseIcon = (phase: string) => {
    const icons: Record<string, string> = {
      initialization: '🚀',
      memory: '🧠',
      execution: '⚡',
      generation: '💻',
      critic: '🔍',
      judge: '⚖️',
      gates: '🚪',
      complete: '✅',
      error: '❌'
    };
    return icons[phase] || '📌';
  };

  const getPhaseColor = (phase: string) => {
    const colors: Record<string, string> = {
      initialization: 'text-blue-600',
      memory: 'text-purple-600',
      execution: 'text-yellow-600',
      generation: 'text-green-600',
      critic: 'text-indigo-600',
      judge: 'text-pink-600',
      gates: 'text-cyan-600',
      complete: 'text-green-700',
      error: 'text-red-600'
    };
    return colors[phase] || 'text-gray-600';
  };

  // If no phases, show simple message
  if (phases.length === 0 && !streamData) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500 border">
        <p className="text-sm">Enhanced output will appear here when swarm execution begins</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Phase Progress - Core Feature */}
      {phases.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4 border">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <span>⚡</span>
            Execution Phases
          </h3>
          <div className="space-y-2">
            {phases.map((phase, idx) => (
              <div key={idx} className="flex items-start gap-3">
                <span className="text-xl">{getPhaseIcon(phase.phase)}</span>
                <div className="flex-1">
                  <div className={cn('font-medium text-sm', getPhaseColor(phase.phase))}>
                    {phase.phase.charAt(0).toUpperCase() + phase.phase.slice(1)}
                  </div>
                  {phase.token && (
                    <div className="text-xs text-gray-600 mt-1">{phase.token}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Basic Result Summary - Simplified */}
      {finalResult && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 border border-blue-200">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <span>📊</span>
            Execution Summary
          </h3>
          
          <div className="grid grid-cols-2 gap-3 text-sm">
            {finalResult.team_id && (
              <div>
                <span className="text-xs text-gray-500 block">Team</span>
                <div className="font-medium">{finalResult.team_id}</div>
              </div>
            )}
            {finalResult.success !== undefined && (
              <div>
                <span className="text-xs text-gray-500 block">Status</span>
                <div className="font-medium">
                  {finalResult.success ? (
                    <span className="text-green-600 flex items-center gap-1">
                      <span>✅</span> Success
                    </span>
                  ) : (
                    <span className="text-red-600 flex items-center gap-1">
                      <span>❌</span> Failed
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Basic Metrics */}
          {finalResult.orchestrator_result?.result && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="grid grid-cols-2 gap-2 text-xs">
                {finalResult.orchestrator_result.result.quality_score && (
                  <div>
                    <span className="text-gray-500">Quality:</span>{' '}
                    <span className="font-medium">
                      {(finalResult.orchestrator_result.result.quality_score * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
                {finalResult.orchestrator_result.result.execution_time && (
                  <div>
                    <span className="text-gray-500">Time:</span>{' '}
                    <span className="font-medium">
                      {(finalResult.orchestrator_result.result.execution_time * 1000).toFixed(0)}ms
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Raw Data (collapsible) - Essential for debugging */}
      {(phases.length > 0 || finalResult) && (
        <details className="bg-gray-100 rounded-lg p-3 border">
          <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
            <span className="inline-flex items-center gap-1">
              🔧 Debug Data
            </span>
          </summary>
          <pre className="mt-2 text-xs bg-gray-900 text-gray-300 p-3 rounded overflow-x-auto max-h-40">
            {JSON.stringify(finalResult || phases, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}