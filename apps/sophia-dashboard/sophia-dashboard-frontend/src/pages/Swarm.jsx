import { useEffect, useRef, useState } from "react";
import CommandBar from "../components/CommandBar";

export default function Swarm() {
  const [mission, setMission] = useState(null);
  const [lines, setLines] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [agents, setAgents] = useState({
    planner: { status: "idle", progress: 0 },
    coder: { status: "idle", progress: 0 },
    reviewer: { status: "idle", progress: 0 },
    integrator: { status: "idle", progress: 0 },
  });
  const evtRef = useRef(null);
  const logsEndRef = useRef(null);

  const plan = async (goal) => {
    try {
      const res = await fetch("/api/swarm/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal }),
      });
      const data = await res.json();
      setMission(data.mission);
      setLines([]);
      // Reset agents
      setAgents({
        planner: { status: "ready", progress: 0 },
        coder: { status: "pending", progress: 0 },
        reviewer: { status: "pending", progress: 0 },
        integrator: { status: "pending", progress: 0 },
      });
    } catch (error) {
      console.error("Failed to plan mission:", error);
      setLines(prev => [...prev, `❌ Planning failed: ${error.message}`]);
    }
  };

  const run = async () => {
    if (!mission || isRunning) return;
    
    setIsRunning(true);
    setLines([]);
    evtRef.current?.close();

    try {
      const res = await fetch("/api/swarm/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mission }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              handleStreamEvent(data);
            } catch (e) {
              console.warn('Failed to parse SSE data:', line);
            }
          }
        }
      }
    } catch (error) {
      console.error("Failed to run mission:", error);
      setLines(prev => [...prev, `❌ Mission failed: ${error.message}`]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleStreamEvent = (data) => {
    if (data.event === "log") {
      setLines(prev => [...prev, data.message]);
    } else if (data.event === "step_start") {
      setAgents(prev => ({
        ...prev,
        [data.agent]: { status: "running", progress: 25 }
      }));
      setLines(prev => [...prev, `🚀 ${data.agent} starting: ${data.action}`]);
    } else if (data.event === "step_complete") {
      setAgents(prev => ({
        ...prev,
        [data.agent]: { status: "completed", progress: 100 }
      }));
      setLines(prev => [...prev, `✅ ${data.agent} completed: ${data.result}`]);
    } else if (data.event === "error") {
      setLines(prev => [...prev, `❌ Error: ${data.message}`]);
    }
  };

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  useEffect(() => {
    return () => evtRef.current?.close();
  }, []);

  const getAgentStatusColor = (status) => {
    switch (status) {
      case "completed": return "bg-emerald-500";
      case "running": return "bg-blue-500 animate-pulse";
      case "ready": return "bg-yellow-500";
      case "error": return "bg-red-500";
      default: return "bg-gray-500";
    }
  };

  const getAgentIcon = (agent) => {
    const icons = {
      planner: "🎯",
      coder: "⚡",
      reviewer: "🔍", 
      integrator: "🚀"
    };
    return icons[agent] || "🤖";
  };

  return (
    <div className="space-y-6">
      <CommandBar onSubmit={plan} />
      
      {mission && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white mb-1">Mission Planned</h3>
              <p className="text-white/70 text-sm">{mission.goal}</p>
            </div>
            <button
              onClick={run}
              disabled={isRunning}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-medium transition-all duration-200 shadow-lg"
            >
              {isRunning ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Running...
                </div>
              ) : (
                "🚀 Run Mission"
              )}
            </button>
          </div>
          
          {/* Agent Status */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            {Object.entries(agents).map(([agent, info]) => (
              <div key={agent} className="rounded-xl border border-white/10 bg-white/5 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">{getAgentIcon(agent)}</span>
                  <span className="text-white/90 font-medium capitalize">{agent}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${getAgentStatusColor(info.status)}`}></div>
                  <span className="text-xs text-white/60 capitalize">{info.status}</span>
                </div>
                {info.progress > 0 && (
                  <div className="mt-2 bg-white/10 rounded-full h-1">
                    <div 
                      className="bg-gradient-to-r from-indigo-500 to-purple-600 h-1 rounded-full transition-all duration-300"
                      style={{ width: `${info.progress}%` }}
                    ></div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mission Logs */}
      {lines.length > 0 && (
        <div className="rounded-2xl border border-white/10 bg-black/20 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Mission Logs</h3>
          <div className="bg-black/40 rounded-xl p-4 max-h-96 overflow-y-auto font-mono text-sm">
            {lines.map((line, i) => (
              <div key={i} className="text-white/80 mb-1 leading-relaxed">
                <span className="text-white/40 mr-2">{String(i + 1).padStart(3, '0')}</span>
                {line}
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
          <div className="flex justify-between items-center mt-4">
            <span className="text-xs text-white/50">{lines.length} log entries</span>
            <button
              onClick={() => setLines([])}
              className="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white/70 text-xs transition-colors"
            >
              Clear Logs
            </button>
          </div>
        </div>
      )}

      {/* Recent Jobs */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Missions</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
            <div>
              <div className="text-white/90 font-medium">Build user authentication system</div>
              <div className="text-white/50 text-sm">Completed 2 hours ago</div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
              <span className="text-emerald-400 text-sm">Completed</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
            <div>
              <div className="text-white/90 font-medium">Add payment integration</div>
              <div className="text-white/50 text-sm">Started 30 minutes ago</div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="text-blue-400 text-sm">Running</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

