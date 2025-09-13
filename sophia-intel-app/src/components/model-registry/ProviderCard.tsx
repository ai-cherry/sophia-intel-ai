/**
 * Provider Card Component - Individual provider display with health metrics
 * Shows status, models, costs, performance, and configuration options
 */

import React, { useState, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../ui/dialog';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Alert, AlertDescription } from '../ui/alert';
import {
  Activity,
  Clock,
  DollarSign,
  Settings,
  TestTube,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Wifi,
  WifiOff,
  Zap,
  Target,
} from 'lucide-react';

interface ProviderHealthStatus {
  provider: string;
  status: 'active' | 'degraded' | 'offline';
  last_success: string;
  success_rate: number;
  avg_latency_ms: number;
  error_count: number;
  cost_per_1k_tokens: number;
}

interface VirtualKeyConfig {
  provider: string;
  virtual_key: string;
  models: string[];
  fallback_providers: string[];
  max_tokens: number;
  temperature: number;
  retry_count: number;
}

interface PerformanceMetrics {
  provider: string;
  latency_p50: number;
  latency_p95: number;
  latency_p99: number;
  throughput_rpm: number;
  error_rate: number;
  uptime_percentage: number;
}

interface ModelTestRequest {
  provider: string;
  model?: string;
  test_message: string;
}

interface ProviderCardProps {
  provider: ProviderHealthStatus;
  virtualKeyConfig?: VirtualKeyConfig;
  performanceMetrics?: PerformanceMetrics;
  onTest: (request: ModelTestRequest) => Promise<void>;
  onUpdateConfig: (config: VirtualKeyConfig) => Promise<void>;
  className?: string;
}

export const ProviderCard: React.FC<ProviderCardProps> = ({
  provider,
  virtualKeyConfig,
  performanceMetrics,
  onTest,
  onUpdateConfig,
  className = '',
}) => {
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [showTestDialog, setShowTestDialog] = useState(false);
  const [isTestingModel, setIsTestingModel] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [configForm, setConfigForm] = useState<VirtualKeyConfig | null>(null);

  // Initialize form when dialog opens
  React.useEffect(() => {
    if (showConfigDialog && virtualKeyConfig) {
      setConfigForm({ ...virtualKeyConfig });
    }
  }, [showConfigDialog, virtualKeyConfig]);

  // Get status icon and color
  const getStatusDisplay = () => {
    switch (provider.status) {
      case 'active':
        return {
          icon: <CheckCircle className="h-4 w-4" />,
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          badge: 'default',
        };
      case 'degraded':
        return {
          icon: <AlertTriangle className="h-4 w-4" />,
          color: 'text-orange-600',
          bgColor: 'bg-orange-100',
          badge: 'secondary',
        };
      case 'offline':
        return {
          icon: <XCircle className="h-4 w-4" />,
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          badge: 'destructive',
        };
      default:
        return {
          icon: <AlertTriangle className="h-4 w-4" />,
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          badge: 'secondary',
        };
    }
  };

  // Handle test model
  const handleTestModel = useCallback(async (testMessage: string) => {
    try {
      setIsTestingModel(true);
      setTestResult(null);

      await onTest({
        provider: provider.provider,
        test_message: testMessage,
      });

      setTestResult('✅ Connection test successful!');
    } catch (error) {
      setTestResult(`❌ Test failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsTestingModel(false);
    }
  }, [onTest, provider.provider]);

  // Handle config update
  const handleUpdateConfig = useCallback(async () => {
    if (!configForm) return;

    try {
      await onUpdateConfig(configForm);
      setShowConfigDialog(false);
      setTestResult('✅ Configuration updated successfully!');
    } catch (error) {
      setTestResult(`❌ Update failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [configForm, onUpdateConfig]);

  const statusDisplay = getStatusDisplay();
  const lastSuccessTime = new Date(provider.last_success);
  const isRecent = Date.now() - lastSuccessTime.getTime() < 5 * 60 * 1000; // 5 minutes

  return (
    <Card className={`h-full transition-all duration-200 hover:shadow-md ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <div className={`p-2 rounded-full ${statusDisplay.bgColor}`}>
              <div className={statusDisplay.color}>
                {statusDisplay.icon}
              </div>
            </div>
            <div>
              <CardTitle className="text-lg capitalize">{provider.provider}</CardTitle>
              <CardDescription className="text-xs">
                {virtualKeyConfig?.models.length || 0} models available
              </CardDescription>
            </div>
          </div>
          <Badge variant={statusDisplay.badge as any}>
            {provider.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-green-600" />
            <div>
              <div className="font-medium">{provider.success_rate.toFixed(1)}%</div>
              <div className="text-xs text-gray-500">Success Rate</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-blue-600" />
            <div>
              <div className="font-medium">{provider.avg_latency_ms.toFixed(0)}ms</div>
              <div className="text-xs text-gray-500">Avg Latency</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-green-600" />
            <div>
              <div className="font-medium">${provider.cost_per_1k_tokens.toFixed(4)}</div>
              <div className="text-xs text-gray-500">Per 1K tokens</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-orange-600" />
            <div>
              <div className="font-medium">{provider.error_count}</div>
              <div className="text-xs text-gray-500">Recent Errors</div>
            </div>
          </div>
        </div>

        {/* Performance Progress Bars */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">Success Rate</span>
            <span className="font-medium">{provider.success_rate.toFixed(1)}%</span>
          </div>
          <Progress
            value={provider.success_rate}
            className="h-2"
          />
        </div>

        {/* Performance Metrics (if available) */}
        {performanceMetrics && (
          <div className="p-3 bg-gray-50 rounded-lg space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Zap className="h-4 w-4 text-purple-600" />
              Performance Metrics
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <div className="text-gray-600">P95 Latency</div>
                <div className="font-medium">{performanceMetrics.latency_p95.toFixed(0)}ms</div>
              </div>
              <div>
                <div className="text-gray-600">Throughput</div>
                <div className="font-medium">{performanceMetrics.throughput_rpm} RPM</div>
              </div>
              <div>
                <div className="text-gray-600">Error Rate</div>
                <div className="font-medium">{performanceMetrics.error_rate.toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-gray-600">Uptime</div>
                <div className="font-medium">{performanceMetrics.uptime_percentage.toFixed(1)}%</div>
              </div>
            </div>
          </div>
        )}

        {/* Models List */}
        {virtualKeyConfig && (
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">Available Models</div>
            <div className="flex flex-wrap gap-1">
              {virtualKeyConfig.models.slice(0, 3).map((model) => (
                <Badge key={model} variant="outline" className="text-xs">
                  {model.split('/').pop() || model}
                </Badge>
              ))}
              {virtualKeyConfig.models.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{virtualKeyConfig.models.length - 3} more
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Last Success */}
        <div className="text-xs text-gray-500 flex items-center gap-2">
          {isRecent ? (
            <Wifi className="h-3 w-3 text-green-500" />
          ) : (
            <WifiOff className="h-3 w-3 text-orange-500" />
          )}
          Last success: {lastSuccessTime.toLocaleString()}
        </div>

        {/* Test Result */}
        {testResult && (
          <Alert>
            <AlertDescription className="text-sm">
              {testResult}
            </AlertDescription>
          </Alert>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 pt-2">
          {/* Test Model Button */}
          <Dialog open={showTestDialog} onOpenChange={setShowTestDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="flex-1">
                <TestTube className="h-4 w-4 mr-2" />
                Test
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Test {provider.provider} Provider</DialogTitle>
                <DialogDescription>
                  Send a test message to verify the provider connection and response
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <Textarea
                  placeholder="Enter test message..."
                  defaultValue="Hello, this is a test message. Please respond with a brief acknowledgment."
                  id="testMessage"
                />
                <div className="flex gap-2">
                  <Button
                    onClick={() => {
                      const textarea = document.getElementById('testMessage') as HTMLTextAreaElement;
                      handleTestModel(textarea.value);
                    }}
                    disabled={isTestingModel}
                    className="flex-1"
                  >
                    {isTestingModel ? (
                      <>
                        <Activity className="h-4 w-4 mr-2 animate-spin" />
                        Testing...
                      </>
                    ) : (
                      <>
                        <TestTube className="h-4 w-4 mr-2" />
                        Run Test
                      </>
                    )}
                  </Button>
                  <Button variant="outline" onClick={() => setShowTestDialog(false)}>
                    Cancel
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          {/* Configure Button */}
          <Dialog open={showConfigDialog} onOpenChange={setShowConfigDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="flex-1">
                <Settings className="h-4 w-4 mr-2" />
                Configure
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Configure {provider.provider} Provider</DialogTitle>
                <DialogDescription>
                  Update virtual key settings, model configuration, and parameters
                </DialogDescription>
              </DialogHeader>

              {configForm && (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium">Virtual Key</label>
                      <Input
                        value={configForm.virtual_key}
                        onChange={(e) => setConfigForm({ ...configForm, virtual_key: e.target.value })}
                        placeholder="Virtual key ID"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium">Max Tokens</label>
                      <Input
                        type="number"
                        value={configForm.max_tokens}
                        onChange={(e) => setConfigForm({ ...configForm, max_tokens: parseInt(e.target.value) })}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium">Temperature</label>
                      <Input
                        type="number"
                        step="0.1"
                        min="0"
                        max="2"
                        value={configForm.temperature}
                        onChange={(e) => setConfigForm({ ...configForm, temperature: parseFloat(e.target.value) })}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium">Retry Count</label>
                      <Input
                        type="number"
                        min="1"
                        max="10"
                        value={configForm.retry_count}
                        onChange={(e) => setConfigForm({ ...configForm, retry_count: parseInt(e.target.value) })}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium">Available Models (one per line)</label>
                    <Textarea
                      value={configForm.models.join('\n')}
                      onChange={(e) => setConfigForm({
                        ...configForm,
                        models: e.target.value.split('\n').filter(m => m.trim())
                      })}
                      placeholder="gpt-4-turbo&#10;gpt-4o&#10;gpt-3.5-turbo"
                      rows={4}
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium">Fallback Providers (one per line)</label>
                    <Textarea
                      value={configForm.fallback_providers.join('\n')}
                      onChange={(e) => setConfigForm({
                        ...configForm,
                        fallback_providers: e.target.value.split('\n').filter(p => p.trim())
                      })}
                      placeholder="anthropic&#10;openrouter"
                      rows={3}
                    />
                  </div>

                  <div className="flex gap-2">
                    <Button onClick={handleUpdateConfig} className="flex-1">
                      <Settings className="h-4 w-4 mr-2" />
                      Update Configuration
                    </Button>
                    <Button variant="outline" onClick={() => setShowConfigDialog(false)}>
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </CardContent>
    </Card>
  );
};
