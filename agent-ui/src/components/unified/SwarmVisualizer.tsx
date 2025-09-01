/**
 * Swarm Visualizer Component
 * Real-time visualization of swarm execution with agent flows and debate tracking
 */

import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, 
  Users, 
  MessageSquare, 
  CheckCircle, 
  XCircle,
  AlertCircle,
  Clock,
  Zap,
  Brain
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

interface SwarmVisualizationData {
  execution_id: string;
  swarm_type: string;
  current_step: string;
  progress: number;
  agent_states: Record<string, string>;
  debate_flow: Array<{
    step: number;
    type: string;
    data?: any;
    verdict?: string;
    confidence?: number;
    timestamp: string;
  }>;
  metrics: Record<string, number>;
  patterns_active: string[];
}

interface SwarmVisualizerProps {
  data: SwarmVisualizationData | null;
  onStepClick?: (step: any) => void;
}

export const SwarmVisualizer: React.FC<SwarmVisualizerProps> = ({ 
  data, 
  onStepClick 
}) => {
  const [selectedStep, setSelectedStep] = useState<number | null>(null);
  const [animationPhase, setAnimationPhase] = useState(0);

  useEffect(() => {
    if (data?.progress) {
      setAnimationPhase(Math.floor(data.progress * 10));
    }
  }, [data?.progress]);

  const getStepIcon = (type: string, verdict?: string) => {
    switch (type) {
      case 'proposal':
        return <Brain className="w-4 h-4" />;
      case 'critic':
        return verdict === 'pass' ? 
          <CheckCircle className="w-4 h-4 text-green-500" /> :
          <XCircle className="w-4 h-4 text-red-500" />;
      case 'judge':
        return <Users className="w-4 h-4" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  const getAgentColor = (state: string) => {
    switch (state) {
      case 'active':
        return 'bg-blue-500';
      case 'thinking':
        return 'bg-yellow-500';
      case 'complete':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  if (!data) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-gray-500">No swarm execution in progress</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            <h3 className="font-semibold">Swarm Execution</h3>
            <Badge variant="outline">{data.swarm_type}</Badge>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-500">{data.current_step}</span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Progress</span>
            <span>{Math.round(data.progress * 100)}%</span>
          </div>
          <Progress value={data.progress * 100} className="h-2" />
        </div>

        {/* Agent States */}
        <div className="space-y-2">
          <div className="text-sm font-medium">Active Agents</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(data.agent_states).map(([agent, state]) => (
              <motion.div
                key={agent}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="flex items-center gap-1 px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-800"
              >
                <div className={`w-2 h-2 rounded-full ${getAgentColor(state)}`} />
                <span className="text-xs">{agent}</span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Debate Flow Visualization */}
        <div className="space-y-2">
          <div className="text-sm font-medium">Execution Flow</div>
          <div className="relative">
            {/* Flow Timeline */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />
            
            <div className="space-y-3">
              <AnimatePresence>
                {data.debate_flow.map((step, index) => (
                  <motion.div
                    key={step.step}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: index * 0.1 }}
                    className={`flex items-start gap-3 cursor-pointer ${
                      selectedStep === step.step ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                    } p-2 rounded-lg transition-colors`}
                    onClick={() => {
                      setSelectedStep(step.step);
                      onStepClick?.(step);
                    }}
                  >
                    {/* Step Icon */}
                    <div className="relative z-10 flex items-center justify-center w-8 h-8 bg-white dark:bg-gray-800 rounded-full border-2 border-gray-200 dark:border-gray-700">
                      {getStepIcon(step.type, step.verdict)}
                    </div>
                    
                    {/* Step Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium capitalize">
                          {step.type}
                        </span>
                        {step.confidence && (
                          <Badge variant="secondary" className="text-xs">
                            {Math.round(step.confidence * 100)}%
                          </Badge>
                        )}
                        {step.verdict && (
                          <Badge 
                            variant={step.verdict === 'pass' ? 'default' : 'destructive'}
                            className="text-xs"
                          >
                            {step.verdict}
                          </Badge>
                        )}
                      </div>
                      {step.data && (
                        <div className="text-xs text-gray-500 mt-1">
                          {JSON.stringify(step.data).substring(0, 100)}...
                        </div>
                      )}
                    </div>
                    
                    {/* Timestamp */}
                    <div className="text-xs text-gray-400">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Active Patterns */}
        {data.patterns_active.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-medium">Active Patterns</div>
            <div className="flex flex-wrap gap-1">
              {data.patterns_active.map((pattern) => (
                <Badge key={pattern} variant="outline" className="text-xs">
                  <Zap className="w-3 h-3 mr-1" />
                  {pattern}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Metrics */}
        {Object.keys(data.metrics).length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-medium">Performance Metrics</div>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(data.metrics).map(([key, value]) => (
                <div key={key} className="flex justify-between text-xs">
                  <span className="text-gray-500">{key}:</span>
                  <span className="font-mono">
                    {typeof value === 'number' ? value.toFixed(2) : value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};