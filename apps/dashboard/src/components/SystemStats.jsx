import React, { useState, useEffect } from 'react';

const SystemStats = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/v1/system/stats');
        if (!response.ok) {
          throw new Error('Failed to fetch system stats');
        }
        const data = await response.json();
        setStats(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="system-stats loading">
        <div className="loading-spinner">Loading system stats...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="system-stats error">
        <div className="error-message">Error: {error}</div>
      </div>
    );
  }

  const getHealthColor = (health) => {
    switch (health) {
      case 'healthy': return '#4CAF50';
      case 'warning': return '#FF9800';
      case 'error': return '#F44336';
      default: return '#9E9E9E';
    }
  };

  const getUsageColor = (percentage) => {
    if (percentage < 50) return '#4CAF50';
    if (percentage < 80) return '#FF9800';
    return '#F44336';
  };

  return (
    <div className="system-stats">
      <h3>System Statistics</h3>
      
      <div className="stats-grid">
        <div className="stat-card">
          <h4>System Health</h4>
          <div 
            className="health-indicator"
            style={{ 
              backgroundColor: getHealthColor(stats.system_health),
              color: 'white',
              padding: '8px 16px',
              borderRadius: '4px',
              textAlign: 'center',
              fontWeight: 'bold'
            }}
          >
            {stats.system_health.toUpperCase()}
          </div>
        </div>

        <div className="stat-card">
          <h4>Performance</h4>
          <div className="performance-metrics">
            <div className="metric">
              <span>CPU Usage:</span>
              <span style={{ color: getUsageColor(stats.performance.cpu_usage_percent) }}>
                {stats.performance.cpu_usage_percent}%
              </span>
            </div>
            <div className="metric">
              <span>Memory Usage:</span>
              <span style={{ color: getUsageColor(stats.performance.memory_usage_percent) }}>
                {stats.performance.memory_usage_percent}%
              </span>
            </div>
            <div className="metric">
              <span>Disk Usage:</span>
              <span style={{ color: getUsageColor(stats.performance.disk_usage_percent) }}>
                {stats.performance.disk_usage_percent}%
              </span>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <h4>AI Swarm</h4>
          <div className="swarm-info">
            <div className="metric">
              <span>Status:</span>
              <span style={{ 
                color: stats.ai_swarm.status === 'operational' ? '#4CAF50' : '#F44336',
                fontWeight: 'bold'
              }}>
                {stats.ai_swarm.status.toUpperCase()}
              </span>
            </div>
            <div className="metric">
              <span>Active Agents:</span>
              <span>{stats.ai_swarm.active_agents}/{stats.ai_swarm.total_agents}</span>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <h4>Uptime</h4>
          <div className="uptime-info">
            <div className="metric">
              <span>Hours:</span>
              <span>{stats.uptime.hours}</span>
            </div>
            <div className="metric">
              <span>Days:</span>
              <span>{stats.uptime.days}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="version-info">
        <small>Version: {stats.version} | Last Updated: {new Date(stats.timestamp).toLocaleString()}</small>
      </div>

      <style jsx>{`
        .system-stats {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          padding: 20px;
          margin: 20px 0;
          backdrop-filter: blur(10px);
        }

        .system-stats h3 {
          color: white;
          margin-bottom: 20px;
          text-align: center;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 15px;
          margin-bottom: 15px;
        }

        .stat-card {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 6px;
          padding: 15px;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .stat-card h4 {
          color: white;
          margin-bottom: 10px;
          font-size: 14px;
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .metric {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          color: white;
          font-size: 14px;
        }

        .metric span:first-child {
          opacity: 0.8;
        }

        .metric span:last-child {
          font-weight: bold;
        }

        .loading, .error {
          text-align: center;
          padding: 40px;
          color: white;
        }

        .loading-spinner {
          font-size: 16px;
          opacity: 0.8;
        }

        .error-message {
          color: #F44336;
          font-weight: bold;
        }

        .version-info {
          text-align: center;
          color: rgba(255, 255, 255, 0.6);
          margin-top: 15px;
          padding-top: 15px;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
      `}</style>
    </div>
  );
};

export default SystemStats;

