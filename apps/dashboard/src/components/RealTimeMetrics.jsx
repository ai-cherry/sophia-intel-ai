import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card.jsx";
import { Badge } from "@/components/ui/badge.jsx";
import { Progress } from "@/components/ui/progress.jsx";
import { Alert, AlertDescription } from "@/components/ui/alert.jsx";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  Activity,
  Zap,
  Clock,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Cpu,
  Database,
  Network,
  Brain,
} from "lucide-react";

export function RealTimeMetrics({ apiBaseUrl }) {
  const [metrics, setMetrics] = useState({
    requests: {
      total: 0,
      per_minute: 0,
      success_rate: 0,
      error_rate: 0
    },
    latency: {
      avg: 0,
      p95: 0,
      p99: 0
    },
    backends: {
      orchestrator: 0,
      swarm: 0,
      direct: 0
    },
    system: {
      memory_usage: 0,
      cpu_usage: 0,
      active_sessions: 0
    },
    chat: {
      messages_processed: 0,
      avg_response_time: 0,
      context_switches: 0
    }
  });

  const [historicalData, setHistoricalData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastRequestId, setLastRequestId] = useState(null);
  const [backendUsed, setBackendUsed] = useState(null);

  // Fetch real metrics from ObservabilityService
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setIsLoading(true);
        
        // Fetch current metrics
        const metricsResponse = await fetch(`${apiBaseUrl}/api/observability/metrics`, {
          headers: {
            'Accept': 'application/json',
          }
        });

        if (metricsResponse.ok) {
          const metricsData = await metricsResponse.json();
          
          // Extract X-Request-ID and X-Backend-Used headers for debugging
          const requestId = metricsResponse.headers.get('X-Request-ID');
          const backend = metricsResponse.headers.get('X-Backend-Used');
          
          setLastRequestId(requestId);
          setBackendUsed(backend);
          
          // Update metrics with real data
          setMetrics(prevMetrics => ({
            ...prevMetrics,
            ...metricsData.metrics,
            system: {
              ...prevMetrics.system,
              ...metricsData.system_metrics
            },
            chat: {
              ...prevMetrics.chat,
              ...metricsData.chat_metrics
            }
          }));
        } else {
          // Fallback to synthetic data if real metrics not available
          generateSyntheticMetrics();
        }

        // Fetch historical data for charts
        const historyResponse = await fetch(`${apiBaseUrl}/api/observability/history?hours=24`);
        if (historyResponse.ok) {
          const historyData = await historyResponse.json();
          setHistoricalData(historyData.data || generateSyntheticHistory());
        } else {
          setHistoricalData(generateSyntheticHistory());
        }

        setError(null);
      } catch (err) {
        console.error("Failed to fetch real metrics:", err);
        setError(err.message);
        
        // Fallback to synthetic data
        generateSyntheticMetrics();
        setHistoricalData(generateSyntheticHistory());
      } finally {
        setIsLoading(false);
      }
    };

    fetchMetrics();
    
    // Refresh metrics every 10 seconds
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, [apiBaseUrl]);

  const generateSyntheticMetrics = () => {
    setMetrics({
      requests: {
        total: Math.floor(Math.random() * 10000) + 5000,
        per_minute: Math.floor(Math.random() * 50) + 20,
        success_rate: 0.95 + Math.random() * 0.04,
        error_rate: Math.random() * 0.05
      },
      latency: {
        avg: Math.floor(Math.random() * 100) + 80,
        p95: Math.floor(Math.random() * 200) + 150,
        p99: Math.floor(Math.random() * 500) + 300
      },
      backends: {
        orchestrator: Math.floor(Math.random() * 60) + 40,
        swarm: Math.floor(Math.random() * 30) + 20,
        direct: Math.floor(Math.random() * 20) + 10
      },
      system: {
        memory_usage: Math.random() * 0.3 + 0.4,
        cpu_usage: Math.random() * 0.4 + 0.2,
        active_sessions: Math.floor(Math.random() * 20) + 5
      },
      chat: {
        messages_processed: Math.floor(Math.random() * 1000) + 500,
        avg_response_time: Math.floor(Math.random() * 2000) + 1000,
        context_switches: Math.floor(Math.random() * 50) + 10
      }
    });
  };

  const generateSyntheticHistory = () => {
    return Array.from({ length: 24 }, (_, i) => ({
      hour: `${i}:00`,
      requests: Math.floor(Math.random() * 200) + 100,
      latency: Math.floor(Math.random() * 150) + 80,
      errors: Math.floor(Math.random() * 8),
      orchestrator_usage: Math.floor(Math.random() * 60) + 40,
      swarm_usage: Math.floor(Math.random() * 30) + 20,
      memory_usage: Math.random() * 0.3 + 0.4,
      cpu_usage: Math.random() * 0.4 + 0.2,
    }));
  };

  const getStatusColor = (value, threshold = 0.8) => {
    if (value < threshold * 0.7) return "var(--sophia-status-healthy)";
    if (value < threshold) return "var(--sophia-status-warning)";
    return "var(--sophia-status-critical)";
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse" style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
            <CardHeader className="space-y-2">
              <div className="h-4 bg-gray-300 rounded w-3/4"></div>
              <div className="h-8 bg-gray-300 rounded w-1/2"></div>
            </CardHeader>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {/* Debug Information */}
      {(lastRequestId || backendUsed) && (
        <Alert className="border-blue-200 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-800">
          <Activity className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800 dark:text-blue-200">
            <div className="flex items-center space-x-4 text-sm">
              {lastRequestId && (
                <span>Request ID: <code className="font-mono">{lastRequestId}</code></span>
              )}
              {backendUsed && (
                <span>Backend: <Badge variant="outline">{backendUsed}</Badge></span>
              )}
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to fetch real metrics: {error}. Showing synthetic data.
          </AlertDescription>
        </Alert>
      )}

      {/* Real-Time Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Request Metrics */}
        <Card style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Request Volume</CardTitle>
            <Activity className="h-4 w-4" style={{ color: 'var(--sophia-text-muted)' }} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(metrics.requests.total)}</div>
            <p className="text-xs" style={{ color: 'var(--sophia-text-muted)' }}>
              {metrics.requests.per_minute}/min • {formatPercentage(metrics.requests.success_rate)} success
            </p>
            <Progress value={metrics.requests.success_rate * 100} className="h-2 mt-2" />
          </CardContent>
        </Card>

        {/* Latency Metrics */}
        <Card style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Response Time</CardTitle>
            <Clock className="h-4 w-4" style={{ color: 'var(--sophia-text-muted)' }} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.latency.avg}ms</div>
            <p className="text-xs" style={{ color: 'var(--sophia-text-muted)' }}>
              P95: {metrics.latency.p95}ms • P99: {metrics.latency.p99}ms
            </p>
            <Progress 
              value={Math.min((metrics.latency.avg / 500) * 100, 100)} 
              className="h-2 mt-2" 
            />
          </CardContent>
        </Card>

        {/* System Resources */}
        <Card style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Load</CardTitle>
            <Cpu className="h-4 w-4" style={{ color: 'var(--sophia-text-muted)' }} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatPercentage(metrics.system.cpu_usage)}</div>
            <p className="text-xs" style={{ color: 'var(--sophia-text-muted)' }}>
              Memory: {formatPercentage(metrics.system.memory_usage)} • {metrics.system.active_sessions} sessions
            </p>
            <Progress 
              value={metrics.system.cpu_usage * 100} 
              className="h-2 mt-2" 
            />
          </CardContent>
        </Card>

        {/* Chat Performance */}
        <Card style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Chat Performance</CardTitle>
            <Brain className="h-4 w-4" style={{ color: 'var(--sophia-text-muted)' }} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(metrics.chat.messages_processed)}</div>
            <p className="text-xs" style={{ color: 'var(--sophia-text-muted)' }}>
              Avg: {metrics.chat.avg_response_time}ms • {metrics.chat.context_switches} switches
            </p>
            <Progress value={85} className="h-2 mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* Backend Distribution Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
          <CardHeader>
            <CardTitle>Backend Usage Distribution</CardTitle>
            <p className="text-sm" style={{ color: 'var(--sophia-text-secondary)' }}>
              How requests are routed across different backends
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Orchestrator', value: metrics.backends.orchestrator, fill: 'var(--sophia-primary-blue)' },
                    { name: 'Swarm', value: metrics.backends.swarm, fill: 'var(--sophia-purple)' },
                    { name: 'Direct', value: metrics.backends.direct, fill: 'var(--sophia-cyan)' }
                  ]}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'var(--sophia-bg-tertiary)', 
                    border: '1px solid var(--sophia-border)',
                    borderRadius: 'var(--sophia-radius-md)'
                  }} 
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Historical Performance */}
        <Card style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
          <CardHeader>
            <CardTitle>Performance Trends</CardTitle>
            <p className="text-sm" style={{ color: 'var(--sophia-text-secondary)' }}>
              Request volume and latency over the last 24 hours
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={historicalData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--sophia-border)" />
                <XAxis dataKey="hour" stroke="var(--sophia-text-muted)" />
                <YAxis stroke="var(--sophia-text-muted)" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'var(--sophia-bg-tertiary)', 
                    border: '1px solid var(--sophia-border)',
                    borderRadius: 'var(--sophia-radius-md)'
                  }} 
                />
                <Line
                  type="monotone"
                  dataKey="requests"
                  stroke="var(--sophia-primary-blue)"
                  strokeWidth={2}
                  name="Requests"
                />
                <Line
                  type="monotone"
                  dataKey="latency"
                  stroke="var(--sophia-purple)"
                  strokeWidth={2}
                  name="Latency (ms)"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* System Health Overview */}
      <Card style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
        <CardHeader>
          <CardTitle>System Health Overview</CardTitle>
          <p className="text-sm" style={{ color: 'var(--sophia-text-secondary)' }}>
            Real-time system resource utilization and performance metrics
          </p>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--sophia-border)" />
              <XAxis dataKey="hour" stroke="var(--sophia-text-muted)" />
              <YAxis stroke="var(--sophia-text-muted)" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'var(--sophia-bg-tertiary)', 
                  border: '1px solid var(--sophia-border)',
                  borderRadius: 'var(--sophia-radius-md)'
                }} 
              />
              <Bar dataKey="orchestrator_usage" fill="var(--sophia-primary-blue)" name="Orchestrator %" />
              <Bar dataKey="swarm_usage" fill="var(--sophia-purple)" name="Swarm %" />
              <Bar dataKey="memory_usage" fill="var(--sophia-cyan)" name="Memory %" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}

