'use client';

import { useState, useEffect } from 'react';

interface OutputPhase {
  phase: string;
  token: string;
  critic?: any;
  judge?: any;
  gates?: any;
  final?: any;
}

export function EnhancedOutput({ streamData }: { streamData: string }) {
  const [phases, setPhases] = useState<OutputPhase[]>([]);
  const [finalResult, setFinalResult] = useState<any>(null);

  useEffect(() => {
    if (!streamData) return;

    // Parse the streaming data
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

  return (
    <div className="space-y-4">
      {/* Phase Progress */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Execution Phases</h3>
        <div className="space-y-2">
          {phases.map((phase, idx) => (
            <div key={idx} className="flex items-start gap-3">
              <span className="text-xl">{getPhaseIcon(phase.phase)}</span>
              <div className="flex-1">
                <div className={`font-medium ${getPhaseColor(phase.phase)}`}>
                  {phase.phase.charAt(0).toUpperCase() + phase.phase.slice(1)}
                </div>
                <div className="text-sm text-gray-600">{phase.token}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Critic Analysis */}
      {phases.find(p => p.critic) && (
        <div className="bg-blue-50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">🔍 Critic Analysis</h3>
          <div className="space-y-1">
            <div className="text-sm">
              <span className="font-medium">Verdict:</span>{' '}
              <span className={phases.find(p => p.critic)?.critic.verdict === 'pass' ? 'text-green-600' : 'text-red-600'}>
                {phases.find(p => p.critic)?.critic.verdict?.toUpperCase()}
              </span>
            </div>
            <div className="text-sm">
              <span className="font-medium">Confidence:</span>{' '}
              {(phases.find(p => p.critic)?.critic.confidence_score * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      )}

      {/* Judge Decision */}
      {phases.find(p => p.judge) && (
        <div className="bg-purple-50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-purple-900 mb-2">⚖️ Judge Decision</h3>
          <div className="space-y-1">
            <div className="text-sm">
              <span className="font-medium">Decision:</span>{' '}
              <span className={phases.find(p => p.judge)?.judge.decision === 'accept' ? 'text-green-600' : 'text-red-600'}>
                {phases.find(p => p.judge)?.judge.decision?.toUpperCase()}
              </span>
            </div>
            <div className="text-sm">
              <span className="font-medium">Confidence:</span>{' '}
              {(phases.find(p => p.judge)?.judge.confidence_score * 100).toFixed(1)}%
            </div>
            {phases.find(p => p.judge)?.judge.runner_instructions && (
              <div className="text-sm mt-2">
                <span className="font-medium">Instructions:</span>
                <ul className="list-disc list-inside mt-1">
                  {phases.find(p => p.judge)?.judge.runner_instructions.map((inst: string, i: number) => (
                    <li key={i} className="text-gray-600">{inst}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Gates Status */}
      {phases.find(p => p.gates) && (
        <div className="bg-green-50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-green-900 mb-2">🚪 Gates Status</h3>
          <div className="text-sm">
            <span className="font-medium">Status:</span>{' '}
            <span className={phases.find(p => p.gates)?.gates.allowed ? 'text-green-600' : 'text-red-600'}>
              {phases.find(p => p.gates)?.gates.status}
            </span>
          </div>
        </div>
      )}

      {/* Final Result */}
      {finalResult && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 border border-blue-200">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">📊 Final Result</h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-xs text-gray-500">Team Used</span>
              <div className="font-medium">{finalResult.team_id}</div>
            </div>
            <div>
              <span className="text-xs text-gray-500">Execution Type</span>
              <div className="font-medium">{finalResult.real_execution ? 'Real' : 'Simulated'}</div>
            </div>
            <div>
              <span className="text-xs text-gray-500">Context Items</span>
              <div className="font-medium">{finalResult.context_used || 0}</div>
            </div>
            <div>
              <span className="text-xs text-gray-500">Success</span>
              <div className="font-medium">
                {finalResult.success ? (
                  <span className="text-green-600">✅ Yes</span>
                ) : (
                  <span className="text-red-600">❌ No</span>
                )}
              </div>
            </div>
          </div>

          {/* Orchestrator Details */}
          {finalResult.orchestrator_result && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h4 className="text-xs font-semibold text-gray-700 mb-2">Orchestrator Details</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500">Quality Score:</span>{' '}
                  <span className="font-medium">
                    {(finalResult.orchestrator_result.result?.quality_score * 100 || 0).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Execution Time:</span>{' '}
                  <span className="font-medium">
                    {(finalResult.orchestrator_result.result?.execution_time * 1000 || 0).toFixed(2)}ms
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Swarm Used:</span>{' '}
                  <span className="font-medium">
                    {finalResult.orchestrator_result.result?.swarm_used || 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Rounds:</span>{' '}
                  <span className="font-medium">
                    {finalResult.orchestrator_result.result?.rounds_required || 0}
                  </span>
                </div>
              </div>
              
              {/* Agent Roles */}
              {finalResult.orchestrator_result.result?.agent_roles && (
                <div className="mt-2">
                  <span className="text-xs text-gray-500">Agent Roles:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {finalResult.orchestrator_result.result.agent_roles.map((role: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 bg-gray-100 text-xs rounded-full">
                        {role}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Solution/Output */}
          {finalResult.orchestrator_result?.result?.result?.solution && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h4 className="text-xs font-semibold text-gray-700 mb-2">Generated Solution</h4>
              <div className="bg-gray-800 text-green-400 p-3 rounded text-xs font-mono overflow-x-auto">
                <pre>{finalResult.orchestrator_result.result.result.solution}</pre>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Raw JSON (collapsible) */}
      <details className="bg-gray-100 rounded-lg p-4">
        <summary className="cursor-pointer text-sm font-medium text-gray-700">
          View Raw Response
        </summary>
        <pre className="mt-2 text-xs bg-gray-900 text-gray-300 p-3 rounded overflow-x-auto">
          {JSON.stringify(finalResult || phases, null, 2)}
        </pre>
      </details>
    </div>
  );
}