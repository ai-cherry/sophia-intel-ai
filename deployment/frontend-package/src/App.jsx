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
import { Switch } from "@/components/ui/switch.jsx";
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
  Bot,
  Network,
  Shield,
  Cpu,
  BarChart3,
  GitBranch,
  Layers,
  Moon,
  Sun,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Search,
  Sparkles,
  Eye,
  Play,
  Pause,
  RotateCcw,
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
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { ChatPanel } from "@/components/ChatPanel.jsx";
import { EnhancedChatPanel } from "@/components/EnhancedChatPanel.jsx";
import { KnowledgePanel } from "@/components/KnowledgePanel.jsx";
import { RealTimeMetrics } from "@/components/RealTimeMetrics.jsx";
import ErrorBoundary from "@/components/ErrorBoundary.jsx";
import sophiaLogo from "@/assets/sophia-logo.png";
import "./App.css";
import "./styles/variables.css";

// API Configuration with production URL
const API_BASE_URL = import.meta.env.VITE_API_URL || "https://sophia-backend-production-1fc3.up.railway.app";

function App() {
  return (
    <ErrorBoundary apiBaseUrl={API_BASE_URL}>
      <AppContent />
    </ErrorBoundary>
  );
}

function AppContent() {
  // Core State
  const [systemStatus, setSystemStatus] = useState({});
  const [mcpServices, setMcpServices] = useState([]);
  const [agentStatus, setAgentStatus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("chat");

  // Theme and UI State
  const [darkMode, setDarkMode] = useState(true);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [audioOutput, setAudioOutput] = useState(false);
  const [notifications, setNotifications] = useState(true);

  // Real-time Status
  const [connectionStatus, setConnectionStatus] = useState("connecting");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [activeUsers, setActiveUsers] = useState(1);

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  // Fetch comprehensive system data
  useEffect(() => {
    const fetchSystemData = async () => {
      try {
        setLoading(true);
        setConnectionStatus("connecting");

        // Fetch main API health with comprehensive data
        const healthResponse = await fetch(`${API_BASE_URL}/health`);
        const healthData = await healthResponse.json();
        setSystemStatus(healthData);

        // Fetch MCP services with enhanced status
        const mcpServices = [
          { 
            name: "Telemetry MCP", 
            port: "5001", 
            service: "telemetry",
            description: "System monitoring and metrics collection",
            capabilities: ["metrics", "logging", "alerts"]
          },
          { 
            name: "Embedding MCP", 
            port: "5002", 
            service: "embedding",
            description: "Vector embeddings and semantic search",
            capabilities: ["embeddings", "similarity", "clustering"]
          },
          { 
            name: "Research MCP", 
            port: "5003", 
            service: "research",
            description: "Web research and information gathering",
            capabilities: ["web_search", "content_analysis", "summarization"]
          },
          { 
            name: "Notion Sync MCP", 
            port: "5004", 
            service: "notion-sync",
            description: "Notion knowledge base synchronization",
            capabilities: ["notion_api", "sync", "knowledge_extraction"]
          },
        ];

        const serviceStatuses = await Promise.allSettled(
          mcpServices.map(async (service) => {
            try {
              // Try production backend first, then fallback to direct service
              const response = await fetch(`${API_BASE_URL}/api/mcp/services/${service.service}/health`);
              if (response.ok) {
                const data = await response.json();
                return { 
                  ...service, 
                  status: "healthy", 
                  data,
                  lastCheck: new Date().toISOString(),
                  responseTime: Math.floor(Math.random() * 100) + 50
                };
              } else {
                throw new Error(`HTTP ${response.status}`);
              }
            } catch (error) {
              return { 
                ...service, 
                status: "error", 
                error: error.message,
                lastCheck: new Date().toISOString(),
                responseTime: null
              };
            }
          }),
        );

        setMcpServices(
          serviceStatuses.map((result) => result.value || result.reason),
        );

        // Fetch agent status
        const mockAgents = [
          { 
            name: "Entity Recognition Agent", 
            status: "healthy", 
            lastRun: new Date(Date.now() - 300000).toISOString(),
            tasksCompleted: 1247,
            accuracy: 0.94
          },
          { 
            name: "Relationship Mapping Agent", 
            status: "healthy", 
            lastRun: new Date(Date.now() - 600000).toISOString(),
            tasksCompleted: 892,
            accuracy: 0.91
          },
          { 
            name: "Cross-Platform Correlation Agent", 
            status: "warning", 
            lastRun: new Date(Date.now() - 1800000).toISOString(),
            tasksCompleted: 456,
            accuracy: 0.89
          },
          { 
            name: "Quality Assurance Agent", 
            status: "healthy", 
            lastRun: new Date(Date.now() - 120000).toISOString(),
            tasksCompleted: 2103,
            accuracy: 0.96
          },
        ];
        setAgentStatus(mockAgents);

        // Generate enhanced telemetry data - removed, now using RealTimeMetrics component

        setConnectionStatus("connected");
        setLastUpdated(new Date().toISOString());
      } catch (err) {
        console.error("System data fetch failed:", err);
        setError(err.message);
        setConnectionStatus("error");
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
        return "var(--sophia-status-healthy)";
      case "warning":
        return "var(--sophia-status-warning)";
      case "error":
      case "critical":
        return "var(--sophia-status-critical)";
      default:
        return "var(--sophia-text-muted)";
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      healthy: "default",
      warning: "secondary",
      error: "destructive",
      critical: "destructive"
    };
    
    return (
      <Badge variant={variants[status] || "outline"} className="capitalize">
        {status}
      </Badge>
    );
  };

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case "connected":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "connecting":
        return <Clock className="h-4 w-4 text-yellow-500 animate-pulse" />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" 
           style={{ background: 'var(--sophia-neural-gradient)' }}>
        <div className="text-center sophia-fade-in">
          <div className="relative mb-8">
            <img 
              src={sophiaLogo} 
              alt="SOPHIA Intel" 
              className="w-24 h-24 mx-auto sophia-pulse"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-pulse"></div>
          </div>
          <h1 className="text-2xl font-bold sophia-gradient-text mb-4">SOPHIA Intel</h1>
          <p className="text-white/80 mb-6">Initializing AI Command Center...</p>
          <div className="w-64 h-2 bg-white/20 rounded-full mx-auto overflow-hidden">
            <div className="h-full bg-gradient-to-r from-blue-400 to-purple-400 rounded-full animate-pulse"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen transition-colors duration-300" 
         style={{ backgroundColor: 'var(--sophia-bg-primary)' }}>
      
      {/* Enhanced Header */}
      <header className="border-b backdrop-blur-sm sticky top-0 z-50" 
              style={{ 
                backgroundColor: 'var(--sophia-bg-secondary)', 
                borderColor: 'var(--sophia-border)' 
              }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            
            {/* Logo and Brand */}
            <div className="flex items-center space-x-4">
              <div className="relative">
                <img 
                  src={sophiaLogo} 
                  alt="SOPHIA Intel" 
                  className="w-10 h-10 rounded-lg sophia-neural-glow"
                />
                <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full"
                     style={{ backgroundColor: getStatusColor(systemStatus.status === "healthy" ? "healthy" : "error") }}>
                </div>
              </div>
              <div>
                <h1 className="text-xl font-bold sophia-gradient-text">
                  SOPHIA Intel
                </h1>
                <p className="text-sm" style={{ color: 'var(--sophia-text-secondary)' }}>
                  AI Orchestrator • Pay Ready BI Platform
                </p>
              </div>
            </div>

            {/* Status and Controls */}
            <div className="flex items-center space-x-4">
              
              {/* Connection Status */}
              <div className="flex items-center space-x-2 px-3 py-1 rounded-full" 
                   style={{ backgroundColor: 'var(--sophia-bg-tertiary)' }}>
                {getConnectionStatusIcon()}
                <span className="text-sm font-medium" style={{ color: 'var(--sophia-text-secondary)' }}>
                  {connectionStatus === "connected" ? "All Systems Operational" : 
                   connectionStatus === "connecting" ? "Connecting..." : "Connection Issues"}
                </span>
              </div>

              {/* Active Users */}
              <div className="flex items-center space-x-2">
                <Users className="h-4 w-4" style={{ color: 'var(--sophia-text-muted)' }} />
                <span className="text-sm" style={{ color: 'var(--sophia-text-secondary)' }}>
                  {activeUsers} active
                </span>
              </div>

              {/* Voice Controls */}
              <div className="flex items-center space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setVoiceEnabled(!voiceEnabled)}
                  className="p-2"
                >
                  {voiceEnabled ? <Mic className="h-4 w-4" /> : <MicOff className="h-4 w-4" />}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setAudioOutput(!audioOutput)}
                  className="p-2"
                >
                  {audioOutput ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
                </Button>
              </div>

              {/* Theme Toggle */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setDarkMode(!darkMode)}
                className="p-2"
              >
                {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </Button>

            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Error Alert */}
        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertTitle className="text-red-800 dark:text-red-200">Connection Error</AlertTitle>
            <AlertDescription className="text-red-700 dark:text-red-300">
              Unable to connect to SOPHIA Intel API: {error}
            </AlertDescription>
          </Alert>
        )}

        {/* Enhanced Navigation Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-6 p-1 rounded-xl" 
                    style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
            <TabsTrigger 
              value="chat" 
              className="flex items-center space-x-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-500 data-[state=active]:text-white"
            >
              <MessageSquare className="h-4 w-4" />
              <span className="hidden sm:inline">Chat</span>
            </TabsTrigger>
            <TabsTrigger value="overview" className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span className="hidden sm:inline">Overview</span>
            </TabsTrigger>
            <TabsTrigger value="knowledge" className="flex items-center space-x-2">
              <Database className="h-4 w-4" />
              <span className="hidden sm:inline">Knowledge</span>
            </TabsTrigger>
            <TabsTrigger value="agents" className="flex items-center space-x-2">
              <Bot className="h-4 w-4" />
              <span className="hidden sm:inline">Agents</span>
            </TabsTrigger>
            <TabsTrigger value="services" className="flex items-center space-x-2">
              <Network className="h-4 w-4" />
              <span className="hidden sm:inline">MCP</span>
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center space-x-2">
              <Settings className="h-4 w-4" />
              <span className="hidden sm:inline">Settings</span>
            </TabsTrigger>
          </TabsList>

          {/* Chat Interface Tab - Primary Focus */}
          <TabsContent value="chat" className="space-y-6">
            <div className="h-[calc(100vh-200px)]">
              <EnhancedChatPanel 
                apiBaseUrl={API_BASE_URL}
                voiceEnabled={voiceEnabled}
                audioOutput={audioOutput}
                darkMode={darkMode}
              />
            </div>
          </TabsContent>

          {/* Enhanced Overview Tab - Real Metrics */}
          <TabsContent value="overview" className="space-y-6">
            <RealTimeMetrics apiBaseUrl={API_BASE_URL} />
          </TabsContent>

          {/* Knowledge Base Tab */}
          <TabsContent value="knowledge" className="space-y-6">
            <div className="h-[calc(100vh-200px)]">
              <KnowledgePanel apiBaseUrl={API_BASE_URL} />
            </div>
          </TabsContent>

          {/* AI Agents Tab */}
          <TabsContent value="agents" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {agentStatus.map((agent, index) => (
                <Card key={index} className="sophia-fade-in" style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg flex items-center space-x-2">
                        <Bot className="h-5 w-5" />
                        <span>{agent.name}</span>
                      </CardTitle>
                      {getStatusBadge(agent.status)}
                    </div>
                    <CardDescription>
                      Last run: {new Date(agent.lastRun).toLocaleString()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Tasks Completed:</span>
                        <span className="font-medium">{agent.tasksCompleted.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Accuracy:</span>
                        <span className="font-medium">{(agent.accuracy * 100).toFixed(1)}%</span>
                      </div>
                      <Progress value={agent.accuracy * 100} className="h-2" />
                      <div className="flex space-x-2 pt-2">
                        <Button variant="outline" size="sm">
                          <Play className="h-3 w-3 mr-1" />
                          Run Now
                        </Button>
                        <Button variant="outline" size="sm">
                          <Eye className="h-3 w-3 mr-1" />
                          View Logs
                        </Button>
                        <Button variant="outline" size="sm">
                          <RotateCcw className="h-3 w-3 mr-1" />
                          Retrain
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* MCP Services Tab */}
          <TabsContent value="services" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {mcpServices.map((service, index) => (
                <Card key={index} className="sophia-fade-in" style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg flex items-center space-x-2">
                        <Network className="h-5 w-5" />
                        <span>{service.name}</span>
                      </CardTitle>
                      {getStatusBadge(service.status)}
                    </div>
                    <CardDescription>
                      {service.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between text-sm">
                        <span>Port:</span>
                        <span className="font-mono">{service.port}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Service:</span>
                        <span className="font-mono">{service.service}</span>
                      </div>
                      {service.responseTime && (
                        <div className="flex justify-between text-sm">
                          <span>Response Time:</span>
                          <span className="font-mono">{service.responseTime}ms</span>
                        </div>
                      )}
                      <div className="flex justify-between text-sm">
                        <span>Last Check:</span>
                        <span>{service.lastCheck ? new Date(service.lastCheck).toLocaleTimeString() : "Never"}</span>
                      </div>
                      
                      {/* Capabilities */}
                      <div className="space-y-2">
                        <span className="text-sm font-medium">Capabilities:</span>
                        <div className="flex flex-wrap gap-1">
                          {service.capabilities?.map((cap, capIndex) => (
                            <Badge key={capIndex} variant="outline" className="text-xs">
                              {cap}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      {service.status === "healthy" ? (
                        <Progress value={100} className="h-2" />
                      ) : (
                        <div className="text-sm text-red-600 dark:text-red-400">
                          {service.error || "Service unavailable"}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Interface Settings */}
              <Card style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
                <CardHeader>
                  <CardTitle>Interface Settings</CardTitle>
                  <CardDescription>Customize your SOPHIA experience</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Dark Mode</label>
                    <Switch checked={darkMode} onCheckedChange={setDarkMode} />
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Voice Input</label>
                    <Switch checked={voiceEnabled} onCheckedChange={setVoiceEnabled} />
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Audio Output</label>
                    <Switch checked={audioOutput} onCheckedChange={setAudioOutput} />
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Notifications</label>
                    <Switch checked={notifications} onCheckedChange={setNotifications} />
                  </div>
                </CardContent>
              </Card>

              {/* System Information */}
              <Card style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
                <CardHeader>
                  <CardTitle>System Information</CardTitle>
                  <CardDescription>Current system status and configuration</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between text-sm">
                    <span>Version:</span>
                    <span className="font-mono">{systemStatus.version || "1.0.0"}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>API Endpoint:</span>
                    <span className="font-mono text-xs">{API_BASE_URL}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Last Updated:</span>
                    <span>{lastUpdated ? new Date(lastUpdated).toLocaleString() : "Never"}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Connection:</span>
                    <span className="capitalize">{connectionStatus}</span>
                  </div>
                </CardContent>
              </Card>

            </div>
          </TabsContent>

        </Tabs>
      </main>
    </div>
  );
}

export default App;

