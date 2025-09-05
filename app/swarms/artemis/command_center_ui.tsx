"""
Artemis Command Center UI Component
Military-themed interface with professional tactical styling
"""

import React, { useState, useEffect } from 'react';
import { AlertCircle, Activity, Shield, Target, Radio, CheckCircle, XCircle } from 'lucide-react';
import { SystemVitalsPanel } from './components/SystemVitalsPanel';
import { OperationalReadinessPanel } from './components/OperationalReadinessPanel';

// TypeScript interfaces
interface Unit {
  designation: string;
  status: 'STANDBY' | 'DEPLOYING' | 'ACTIVE' | 'ENGAGED' | 'COMPLETE' | 'CRITICAL' | 'ABORT';
  agents: Agent[];
  progress: number;
}

interface Agent {
  callsign: string;
  rank: string;
  status: 'ready' | 'active' | 'complete';
  currentTask?: string;
}

interface Mission {
  name: string;
  type: string;
  phase: number;
  totalPhases: number;
  startTime: Date;
  estimatedCompletion: Date;
  units: Unit[];
}

// Status indicator component
const StatusIndicator: React.FC<{ status: string }> = ({ status }) => {
  const statusConfig = {
    STANDBY: { color: 'bg-gray-500', pulse: false },
    DEPLOYING: { color: 'bg-yellow-500', pulse: true },
    ACTIVE: { color: 'bg-green-500', pulse: true },
    ENGAGED: { color: 'bg-orange-500', pulse: true },
    CRITICAL: { color: 'bg-red-500', pulse: true },
    COMPLETE: { color: 'bg-blue-500', pulse: false },
    ABORT: { color: 'bg-purple-500', pulse: false },
  };

  const config = statusConfig[status] || statusConfig.STANDBY;

  return (
    <div className="flex items-center space-x-2">
      <div className={`w-3 h-3 rounded-full ${config.color} ${config.pulse ? 'animate-pulse' : ''}`} />
      <span className="text-xs font-mono uppercase">{status}</span>
    </div>
  );
};

// Unit card component
const UnitCard: React.FC<{ unit: Unit }> = ({ unit }) => {
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-3">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-sm font-bold text-green-400 font-mono">{unit.designation}</h3>
          <StatusIndicator status={unit.status} />
        </div>
        <Shield className="w-5 h-5 text-gray-500" />
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-xs text-gray-400">
          <span>OPERATIONAL</span>
          <span>{unit.progress}%</span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-1.5">
          <div
            className="bg-green-500 h-1.5 rounded-full transition-all duration-500"
            style={{ width: `${unit.progress}%` }}
          />
        </div>
      </div>

      <div className="space-y-1">
        {unit.agents.map((agent) => (
          <div key={agent.callsign} className="flex items-center justify-between text-xs">
            <span className="text-gray-300 font-mono">{agent.callsign}</span>
            <span className={`
              ${agent.status === 'ready' ? 'text-gray-400' : ''}
              ${agent.status === 'active' ? 'text-green-400' : ''}
              ${agent.status === 'complete' ? 'text-blue-400' : ''}
            `}>
              {agent.status.toUpperCase()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Mission briefing component
const MissionBriefing: React.FC<{ mission: Mission }> = ({ mission }) => {
  const elapsedTime = new Date().getTime() - mission.startTime.getTime();
  const estimatedTotal = mission.estimatedCompletion.getTime() - mission.startTime.getTime();
  const progressPercent = Math.min((elapsedTime / estimatedTotal) * 100, 100);

  return (
    <div className="bg-gray-900 border-2 border-green-500 rounded-lg p-6 space-y-4">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-xl font-bold text-green-400 font-mono">MISSION BRIEFING</h2>
          <p className="text-sm text-gray-400 mt-1">{mission.name}</p>
        </div>
        <Radio className="w-6 h-6 text-green-500 animate-pulse" />
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-500">OPERATION TYPE</span>
          <p className="text-white font-mono">{mission.type}</p>
        </div>
        <div>
          <span className="text-gray-500">CURRENT PHASE</span>
          <p className="text-white font-mono">{mission.phase}/{mission.totalPhases}</p>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-xs text-gray-400">
          <span>MISSION PROGRESS</span>
          <span>{progressPercent.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-2">
          <div
            className="bg-green-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      <div className="flex justify-between text-xs text-gray-400">
        <span>START: {mission.startTime.toLocaleTimeString()}</span>
        <span>ETA: {mission.estimatedCompletion.toLocaleTimeString()}</span>
      </div>
    </div>
  );
};

// Intelligence feed component
const IntelligenceFeed: React.FC<{ messages: string[] }> = ({ messages }) => {
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 h-64 overflow-hidden">
      <h3 className="text-sm font-bold text-blue-400 mb-3 font-mono">INTELLIGENCE FEED</h3>
      <div className="space-y-2 overflow-y-auto h-48">
        {messages.map((message, index) => (
          <div key={index} className="text-xs text-gray-300 font-mono flex items-start space-x-2">
            <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span>
            <span>{message}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Main Command Center component
export const ArtemisCommandCenter: React.FC = () => {
  const [mission, setMission] = useState<Mission | null>(null);
  const [intelMessages, setIntelMessages] = useState<string[]>([
    'System initialization complete',
    'All units reporting operational status',
    'Secure channels established',
    'Awaiting mission deployment authorization',
  ]);

  // Simulated mission data
  useEffect(() => {
    const mockMission: Mission = {
      name: 'Operation Clean Sweep',
      type: 'FULL_REMEDIATION',
      phase: 2,
      totalPhases: 5,
      startTime: new Date(Date.now() - 10 * 60 * 1000),
      estimatedCompletion: new Date(Date.now() + 50 * 60 * 1000),
      units: [
        {
          designation: "1st Recon Battalion 'Pathfinders'",
          status: 'COMPLETE',
          progress: 100,
          agents: [
            { callsign: 'SCOUT-1', rank: 'Recon Lead', status: 'complete' },
            { callsign: 'SCOUT-2', rank: 'Analyst', status: 'complete' },
            { callsign: 'SCOUT-3', rank: 'Doc Specialist', status: 'complete' },
          ],
        },
        {
          designation: "QC Division 'Sentinels'",
          status: 'ACTIVE',
          progress: 45,
          agents: [
            { callsign: 'SENTINEL-LEAD', rank: 'QC Commander', status: 'active' },
            { callsign: 'VALIDATOR-1', rank: 'Sr Validator', status: 'active' },
            { callsign: 'VALIDATOR-2', rank: 'Security', status: 'ready' },
          ],
        },
        {
          designation: "Strategic Command 'Architects'",
          status: 'STANDBY',
          progress: 0,
          agents: [
            { callsign: 'COMMAND-1', rank: 'Commander', status: 'ready' },
            { callsign: 'COMMAND-2', rank: 'Tactical', status: 'ready' },
            { callsign: 'COMMAND-3', rank: 'Intel Chief', status: 'ready' },
          ],
        },
      ],
    };

    setMission(mockMission);

    // Simulate intelligence feed updates
    const interval = setInterval(() => {
      const messages = [
        'Code conflict detected in module core/auth',
        'Dependency vulnerability scan complete',
        'Performance bottleneck identified in database layer',
        'Architecture pattern analysis in progress',
        'Security clearance verified for all operators',
      ];

      setIntelMessages(prev => [
        messages[Math.floor(Math.random() * messages.length)],
        ...prev.slice(0, 9),
      ]);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      {/* Header */}
      <header className="mb-6 border-b border-gray-800 pb-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <Target className="w-8 h-8 text-green-500" />
            <div>
              <h1 className="text-2xl font-bold font-mono text-green-400">ARTEMIS COMMAND CENTER</h1>
              <p className="text-sm text-gray-500">Code Excellence Operations</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <StatusIndicator status="ACTIVE" />
            <button className="px-4 py-2 bg-red-900 hover:bg-red-800 text-red-300 rounded font-mono text-sm">
              ABORT MISSION
            </button>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left Sidebar - Unit Status */}
        <div className="col-span-3 space-y-4">
          <h2 className="text-sm font-bold text-gray-400 font-mono">UNIT STATUS</h2>
          {mission?.units.map((unit) => (
            <UnitCard key={unit.designation} unit={unit} />
          ))}
        </div>

        {/* Center - Mission Briefing & Map */}
        <div className="col-span-6 space-y-6">
          {mission && <MissionBriefing mission={mission} />}

          {/* Tactical Map Placeholder */}
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 h-96">
            <h3 className="text-sm font-bold text-green-400 mb-3 font-mono">TACTICAL OVERVIEW</h3>
            <div className="bg-gray-950 rounded h-80 flex items-center justify-center border border-gray-800">
              <div className="text-center space-y-2">
                <Activity className="w-12 h-12 text-green-500 mx-auto animate-pulse" />
                <p className="text-sm text-gray-500">Repository scan visualization active</p>
                <p className="text-xs text-gray-600 font-mono">
                  Files: 1,247 | Issues: 23 | Fixed: 18
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar - Intelligence Feed and System Monitoring */}
        <div className="col-span-3 space-y-4">
          <h2 className="text-sm font-bold text-gray-400 font-mono">OPERATIONAL INTELLIGENCE</h2>

          {/* System Vitals Panel */}
          <SystemVitalsPanel refreshInterval={5000} />

          {/* Operational Readiness Panel */}
          <OperationalReadinessPanel refreshInterval={10000} />

          <IntelligenceFeed messages={intelMessages} />

          {/* Command Controls */}
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-3">
            <h3 className="text-sm font-bold text-blue-400 font-mono">COMMAND CONTROLS</h3>
            <button className="w-full px-4 py-2 bg-green-900 hover:bg-green-800 text-green-300 rounded font-mono text-sm">
              DEPLOY NEXT PHASE
            </button>
            <button className="w-full px-4 py-2 bg-yellow-900 hover:bg-yellow-800 text-yellow-300 rounded font-mono text-sm">
              REQUEST REINFORCEMENTS
            </button>
            <button className="w-full px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded font-mono text-sm">
              GENERATE REPORT
            </button>
          </div>
        </div>
      </div>

      {/* Footer Status Bar */}
      <footer className="mt-6 border-t border-gray-800 pt-4">
        <div className="flex justify-between items-center text-xs text-gray-500 font-mono">
          <div className="flex space-x-6">
            <span>SECURE CONNECTION</span>
            <span>ENCRYPTION: AES-256</span>
            <span>CLEARANCE: LEVEL 5</span>
          </div>
          <div className="flex space-x-6">
            <span>UPTIME: 99.98%</span>
            <span>LATENCY: 12ms</span>
            <span>{new Date().toLocaleString()}</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ArtemisCommandCenter;
