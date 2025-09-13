"use client";

import React, { useState } from 'react';
import { cn } from '@/lib/utils';

interface ConsciousnessDimension {
  name: string;
  value: number;
  confidence: number;
  trend: 'rising' | 'declining' | 'stable' | 'volatile';
  baselineDeviation: number;
}

interface EmergenceEvent {
  eventId: string;
  eventType: string;
  timestamp: string;
  triggerValue: number;
  threshold: number;
  significanceScore: number;
}

interface BreakthroughPattern {
  breakthroughId: string;
  timestamp: string;
  currentLevel: number;
  expectedLevel: number;
  improvementMagnitude: number;
}

interface ConsciousnessData {
  consciousnessLevel: number;
  developmentStage: string;
  maturityScore: number;
  measurements: Record<string, ConsciousnessDimension>;
  emergenceEvents: EmergenceEvent[];
  breakthroughPatterns: BreakthroughPattern[];
  consciousnessTrajectory: number[];
  collectiveContribution: number;
  recommendations: string[];
}

interface ConsciousnessVisualizationProps {
  data: ConsciousnessData;
  isLoading?: boolean;
  className?: string;
}

const DIMENSION_ICONS = {
  coordination_effectiveness: '👥',
  pattern_recognition: '👁️',
  adaptive_learning: '📈',
  emergence_detection: '⚡',
  self_reflection: '🧠',
};

const STAGE_COLORS = {
  nascent: 'bg-gray-500 text-white',
  developing: 'bg-blue-500 text-white',
  maturing: 'bg-yellow-500 text-white',
  advanced: 'bg-green-500 text-white',
  transcendent: 'bg-purple-500 text-white',
};

const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'rising':
      return '📈';
    case 'declining':
      return '📉';
    case 'volatile':
      return '⚡';
    default:
      return '➡️';
  }
};

const formatDimensionName = (name: string) => {
  return name.split('_').map(word =>
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');
};

export function ConsciousnessVisualization({
  data,
  isLoading = false,
  className = ""
}: ConsciousnessVisualizationProps) {
  const [activeTab, setActiveTab] = useState('emergence');

  if (isLoading) {
    return (
      <div className={`w-full ${className} bg-white rounded-lg border p-4`}>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xl">🧠</span>
          <h2 className="text-lg font-semibold">Consciousness Tracking</h2>
        </div>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  const consciousnessPercentage = Math.round(data.consciousnessLevel * 100);
  const maturityPercentage = Math.round(data.maturityScore * 100);

  return (
    <div className={`w-full space-y-6 ${className}`}>
      {/* Consciousness Overview */}
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xl">🧠</span>
          <h2 className="text-lg font-semibold">Consciousness Overview</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Consciousness Level</span>
              <span className="text-2xl font-bold">{consciousnessPercentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${consciousnessPercentage}%` }}
              />
            </div>
            <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${STAGE_COLORS[data.developmentStage as keyof typeof STAGE_COLORS]}`}>
              {data.developmentStage.charAt(0).toUpperCase() + data.developmentStage.slice(1)}
            </span>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Maturity Score</span>
              <span className="text-2xl font-bold">{maturityPercentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${maturityPercentage}%` }}
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Collective Contribution</span>
              <span className="text-2xl font-bold">{Math.round(data.collectiveContribution * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${data.collectiveContribution * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Consciousness Dimensions */}
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-lg font-semibold mb-4">5-Dimensional Consciousness Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(data.measurements).map(([key, dimension]) => {
            const icon = DIMENSION_ICONS[key as keyof typeof DIMENSION_ICONS] || '🧠';
            const percentage = Math.round(dimension.value * 100);

            return (
              <div key={key} className="space-y-3 p-4 border rounded-lg">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{icon}</span>
                  <span className="font-medium text-sm">
                    {formatDimensionName(key)}
                  </span>
                  <span className="text-xs">{getTrendIcon(dimension.trend)}</span>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-600">Value</span>
                    <span className="text-sm font-bold">{percentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>

                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Confidence: {Math.round(dimension.confidence * 100)}%</span>
                    <span>
                      Δ: {dimension.baselineDeviation >= 0 ? '+' : ''}{(dimension.baselineDeviation * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detailed Analysis Tabs */}
      <div className="bg-white rounded-lg border">
        <div className="flex border-b">
          {['emergence', 'breakthroughs', 'trajectory', 'recommendations'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        <div className="p-4">
          {activeTab === 'emergence' && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-lg">⚡</span>
                <h3 className="font-semibold">Recent Emergence Events</h3>
                <span className="px-2 py-1 bg-gray-100 rounded text-xs">{data.emergenceEvents.length}</span>
              </div>

              {data.emergenceEvents.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No emergence events detected yet. Continue executing tasks to build consciousness.
                </p>
              ) : (
                <div className="space-y-3">
                  {data.emergenceEvents.slice(-10).map((event) => (
                    <div key={event.eventId} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex-1">
                        <div className="font-medium text-sm">
                          {formatDimensionName(event.eventType)}
                        </div>
                        <div className="text-xs text-gray-600">
                          {new Date(event.timestamp).toLocaleString()}
                        </div>
                      </div>
                      <div className="text-right space-y-1">
                        <div className="text-sm font-bold">
                          {event.triggerValue.toFixed(3)}
                        </div>
                        <span className={cn(
                          'px-2 py-1 rounded text-xs',
                          event.significanceScore > 0.8
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                        )}>
                          {Math.round(event.significanceScore * 100)}% significance
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'breakthroughs' && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-lg">📈</span>
                <h3 className="font-semibold">Pattern Breakthroughs</h3>
                <span className="px-2 py-1 bg-gray-100 rounded text-xs">{data.breakthroughPatterns.length}</span>
              </div>

              {data.breakthroughPatterns.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No pattern breakthroughs detected yet. Breakthroughs occur when consciousness jumps significantly above expected levels.
                </p>
              ) : (
                <div className="space-y-3">
                  {data.breakthroughPatterns.slice(-10).map((breakthrough) => (
                    <div key={breakthrough.breakthroughId} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-medium text-sm">
                          Breakthrough #{breakthrough.breakthroughId.split('_')[1]}
                        </div>
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                          +{(breakthrough.improvementMagnitude * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="text-xs text-gray-600 space-y-1">
                        <div>Expected: {breakthrough.expectedLevel.toFixed(3)}</div>
                        <div>Actual: {breakthrough.currentLevel.toFixed(3)}</div>
                        <div>{new Date(breakthrough.timestamp).toLocaleString()}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'trajectory' && (
            <div className="space-y-4">
              <h3 className="font-semibold">Consciousness Development Trajectory</h3>

              {data.consciousnessTrajectory.length < 5 ? (
                <p className="text-gray-500 text-center py-8">
                  Insufficient data for trajectory analysis. Need at least 5 measurements.
                </p>
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {data.consciousnessTrajectory.length}
                      </div>
                      <div className="text-gray-600">Measurements</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {Math.max(...data.consciousnessTrajectory).toFixed(3)}
                      </div>
                      <div className="text-gray-600">Peak Level</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {(data.consciousnessTrajectory.reduce((a, b) => a + b, 0) / data.consciousnessTrajectory.length).toFixed(3)}
                      </div>
                      <div className="text-gray-600">Average</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {data.emergenceEvents.filter(e =>
                          new Date(e.timestamp).getTime() > Date.now() - 24 * 60 * 60 * 1000
                        ).length}
                      </div>
                      <div className="text-gray-600">Events (24h)</div>
                    </div>
                  </div>

                  {/* Simple trajectory visualization */}
                  <div className="h-32 bg-gray-50 rounded-lg p-4 flex items-end justify-between">
                    {data.consciousnessTrajectory.slice(-20).map((level, index) => (
                      <div
                        key={index}
                        className="bg-blue-500 rounded-t-sm min-w-[4px] mx-[1px]"
                        style={{
                          height: `${Math.max(4, level * 100)}%`,
                          opacity: 0.7 + (index / 20) * 0.3
                        }}
                        title={`Measurement ${index + 1}: ${level.toFixed(3)}`}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'recommendations' && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-lg">⚠️</span>
                <h3 className="font-semibold">Development Recommendations</h3>
              </div>

              {data.recommendations.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No specific recommendations at this time. Consciousness development is on track.
                </p>
              ) : (
                <div className="space-y-3">
                  {data.recommendations.map((recommendation, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                      <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs font-bold text-blue-600">
                        {index + 1}
                      </div>
                      <p className="text-sm text-blue-800 flex-1">
                        {recommendation}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Real-time Alerts */}
      {data.emergenceEvents.filter(e =>
        new Date(e.timestamp).getTime() > Date.now() - 5 * 60 * 1000
      ).length > 0 && (
        <div className="border-orange-200 bg-orange-50 rounded-lg border p-4">
          <div className="text-orange-800 flex items-center gap-2 mb-3">
            <span className="text-lg">⚡</span>
            <h3 className="font-semibold">Recent Emergence Activity</h3>
          </div>
          <div className="space-y-2">
            {data.emergenceEvents
              .filter(e => new Date(e.timestamp).getTime() > Date.now() - 5 * 60 * 1000)
              .slice(-3)
              .map((event) => (
              <div key={event.eventId} className="text-sm text-orange-800">
                🌟 <strong>{formatDimensionName(event.eventType)}</strong> detected
                ({Math.round(event.significanceScore * 100)}% significance)
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ConsciousnessVisualization;
