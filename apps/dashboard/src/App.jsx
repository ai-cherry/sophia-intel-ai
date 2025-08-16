import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button.jsx";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card.jsx";
import { Badge } from "@/components/ui/badge.jsx";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs.jsx";
import { Progress } from "@/components/ui/progress.jsx";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert.jsx";
import {
  Activity,
  Brain,
  Database,
  Globe,
  MessageSquare,
  Settings,
  TrendingUp,
  Zap,
  CheckCircle,
  AlertCircle,
  Clock,
  Users,
} from "lucide-react";
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
} from "recharts";
import { ChatPanel } from "@/components/ChatPanel.jsx";
import { WebResearchPanel } from "@/components/WebResearchPanel.jsx";
import { KnowledgePanel } from "@/components/KnowledgePanel.jsx";
import "./App.css";

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [systemStatus, setSystemStatus] = useState({});
  const [mcpServices, setMcpServices] = useState([]);
  const [telemetryData, setTelemetryData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch system status and MCP services
  useEffect(() => {
    const fetchSystemData = async () => {
      try {
        setLoading(true);

        // Fetch main API health
        const healthResponse = await fetch(`${API_BASE_URL}/health`);
        const healthData = await healthResponse.json();
        setSystemStatus(healthData);

        // Fetch MCP services status
        const mcpServices = [
          { name: "Telemetry MCP", port: "5001", service: "telemetry" },
          { name: "Embedding MCP", port: "5002", service: "embedding" },
          { name: "Research MCP", port: "5003", service: "research" },
          { name: "Notion Sync MCP", port: "5004", service: "notion-sync" },
        ];

        const serviceStatuses = await Promise.allSettled(
          mcpServices.map(async (service) => {
            try {
              const response = await fetch(
                `http://104.171.202.107:${service.port}/health`,
              );
              const data = await response.json();
              return { ...service, status: "healthy", data };
            } catch (error) {
              return { ...service, status: "error", error: error.message };
            }
          }),
        );

        setMcpServices(
          serviceStatuses.map((result) => result.value || result.reason),
        );

        // Generate sample telemetry data
        const sampleData = Array.from({ length: 24 }, (_, i) => ({
          hour: `${i}:00`,
          requests: Math.floor(Math.random() * 100) + 50,
          latency: Math.floor(Math.random() * 200) + 100,
          errors: Math.floor(Math.random() * 5),
        }));
        setTelemetryData(sampleData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSystemData();

    // Refresh data every 30 seconds
    const interval = setInterval(fetchSystemData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case "healthy":
        return "bg-green-500";
      case "warning":
        return "bg-yellow-500";
      case "error":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "healthy":
        return <Badge className="bg-green-100 text-green-800">Healthy</Badge>;
      case "warning":
        return <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>;
      case "error":
        return <Badge className="bg-red-100 text-red-800">Error</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Unknown</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading SOPHIA Intel Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  SOPHIA Intel
                </h1>
                <p className="text-sm text-gray-500">
                  AI Command Center Dashboard
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div
                className={`w-3 h-3 rounded-full ${getStatusColor(systemStatus.status === "healthy" ? "healthy" : "error")}`}
              ></div>
              <span className="text-sm text-gray-600">
                {systemStatus.status === "healthy"
                  ? "All Systems Operational"
                  : "System Issues Detected"}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertTitle className="text-red-800">Connection Error</AlertTitle>
            <AlertDescription className="text-red-700">
              Unable to connect to SOPHIA Intel API: {error}
            </AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="services">MCP Services</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="chat">Chat Interface</TabsTrigger>
            <TabsTrigger value="research">Web Research</TabsTrigger>
            <TabsTrigger value="knowledge">Knowledge Base</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* System Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    System Status
                  </CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">
                    Operational
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {systemStatus.version || "v1.0.0"} • Uptime: 99.9%
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    MCP Services
                  </CardTitle>
                  <Zap className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {mcpServices.filter((s) => s.status === "healthy").length}/
                    {mcpServices.length}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Services Online
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    API Requests
                  </CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">1,247</div>
                  <p className="text-xs text-muted-foreground">
                    +12% from last hour
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    Response Time
                  </CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">142ms</div>
                  <p className="text-xs text-muted-foreground">
                    Average latency
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>
                  Common SOPHIA Intel operations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Button
                    variant="outline"
                    className="h-20 flex flex-col items-center justify-center space-y-2"
                  >
                    <MessageSquare className="h-6 w-6" />
                    <span className="text-sm">Start Chat</span>
                  </Button>
                  <Button
                    variant="outline"
                    className="h-20 flex flex-col items-center justify-center space-y-2"
                  >
                    <Globe className="h-6 w-6" />
                    <span className="text-sm">Web Research</span>
                  </Button>
                  <Button
                    variant="outline"
                    className="h-20 flex flex-col items-center justify-center space-y-2"
                  >
                    <Database className="h-6 w-6" />
                    <span className="text-sm">Query Knowledge</span>
                  </Button>
                  <Button
                    variant="outline"
                    className="h-20 flex flex-col items-center justify-center space-y-2"
                  >
                    <Settings className="h-6 w-6" />
                    <span className="text-sm">System Config</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* MCP Services Tab */}
          <TabsContent value="services" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {mcpServices.map((service, index) => (
                <Card key={index}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{service.name}</CardTitle>
                      {getStatusBadge(service.status)}
                    </div>
                    <CardDescription>
                      Port {service.port} • Service: {service.service}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {service.status === "healthy" && service.data ? (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Version:</span>
                          <span>{service.data.version || "1.0.0"}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span>Last Check:</span>
                          <span>
                            {new Date(
                              service.data.timestamp,
                            ).toLocaleTimeString()}
                          </span>
                        </div>
                        <Progress value={100} className="h-2" />
                      </div>
                    ) : (
                      <div className="text-sm text-red-600">
                        {service.error || "Service unavailable"}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>API Request Volume</CardTitle>
                  <CardDescription>
                    Requests per hour over the last 24 hours
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={telemetryData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="hour" />
                      <YAxis />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="requests"
                        stroke="#3b82f6"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Response Latency</CardTitle>
                  <CardDescription>
                    Average response time in milliseconds
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={telemetryData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="hour" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="latency" fill="#10b981" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Chat Interface Tab */}
          <TabsContent value="chat" className="space-y-6">
            <div className="h-[600px]">
              <ChatPanel />
            </div>
          </TabsContent>

          {/* Web Research Tab */}
          <TabsContent value="research" className="space-y-6">
            <div className="h-[600px]">
              <WebResearchPanel />
            </div>
          </TabsContent>

          {/* Knowledge Base Tab */}
          <TabsContent value="knowledge" className="space-y-6">
            <div className="h-[600px]">
              <KnowledgePanel />
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

export default App;
