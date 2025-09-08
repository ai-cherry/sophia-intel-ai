/**
 * Fallback Chain Builder - Visual drag-and-drop interface for configuring failover strategies
 * Supports weight distribution, cost optimization, and latency optimization
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Alert, AlertDescription } from '../ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Separator } from '../ui/separator';
import {
  DragDropContext,
  Droppable,
  Draggable,
  DropResult,
} from '@hello-pangea/dnd';
import {
  ArrowRight,
  ArrowDown,
  Plus,
  X,
  Target,
  DollarSign,
  Zap,
  Settings,
  Save,
  RotateCcw,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Shuffle,
} from 'lucide-react';

interface ProviderHealthStatus {
  provider: string;
  status: 'active' | 'degraded' | 'offline';
  success_rate: number;
  avg_latency_ms: number;
  cost_per_1k_tokens: number;
}

interface FallbackChainConfig {
  primary_provider: string;
  fallback_chain: string[];
  load_balance_weights: Record<string, number>;
  routing_strategy: string;
}

interface RoutingStrategy {
  name: string;
  display_name: string;
  description: string;
}

interface FallbackChainBuilderProps {
  providers: ProviderHealthStatus[];
  fallbackChains: Record<string, FallbackChainConfig>;
  routingStrategies: RoutingStrategy[];
  onUpdateChain: (provider: string, config: FallbackChainConfig) => Promise<void>;
  className?: string;
}

interface ChainItem {
  id: string;
  provider: string;
  weight: number;
  isPrimary: boolean;
}

export const FallbackChainBuilder: React.FC<FallbackChainBuilderProps> = ({
  providers,
  fallbackChains,
  routingStrategies,
  onUpdateChain,
  className = '',
}) => {
  const [selectedPrimary, setSelectedPrimary] = useState<string>('');
  const [currentChain, setCurrentChain] = useState<ChainItem[]>([]);
  const [routingStrategy, setRoutingStrategy] = useState('balanced');
  const [isModified, setIsModified] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  // Initialize with first provider's chain
  useEffect(() => {
    if (providers.length > 0 && !selectedPrimary) {
      const firstProvider = providers[0].provider;
      setSelectedPrimary(firstProvider);
    }
  }, [providers, selectedPrimary]);

  // Load chain when primary provider changes
  useEffect(() => {
    if (selectedPrimary && fallbackChains[selectedPrimary]) {
      const config = fallbackChains[selectedPrimary];
      const chainItems: ChainItem[] = [
        {
          id: `primary-${selectedPrimary}`,
          provider: selectedPrimary,
          weight: config.load_balance_weights[selectedPrimary] || 70,
          isPrimary: true,
        },
        ...config.fallback_chain.map((provider, index) => ({
          id: `fallback-${provider}-${index}`,
          provider,
          weight: config.load_balance_weights[provider] || 30 / config.fallback_chain.length,
          isPrimary: false,
        })),
      ];
      setCurrentChain(chainItems);
      setRoutingStrategy(config.routing_strategy);
      setIsModified(false);
    }
  }, [selectedPrimary, fallbackChains]);

  // Get provider status display
  const getProviderStatus = (providerName: string) => {
    const provider = providers.find(p => p.provider === providerName);
    if (!provider) return { icon: <XCircle className="h-4 w-4" />, color: 'text-gray-400' };

    switch (provider.status) {
      case 'active':
        return { icon: <CheckCircle className="h-4 w-4" />, color: 'text-green-600' };
      case 'degraded':
        return { icon: <AlertTriangle className="h-4 w-4" />, color: 'text-orange-600' };
      case 'offline':
        return { icon: <XCircle className="h-4 w-4" />, color: 'text-red-600' };
      default:
        return { icon: <AlertTriangle className="h-4 w-4" />, color: 'text-gray-400' };
    }
  };

  // Handle drag and drop
  const onDragEnd = useCallback((result: DropResult) => {
    if (!result.destination) return;

    const items = Array.from(currentChain);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    // Don't allow primary to be moved from first position
    const primaryIndex = items.findIndex(item => item.isPrimary);
    if (primaryIndex !== 0) {
      // Move primary back to first position
      const [primary] = items.splice(primaryIndex, 1);
      items.unshift(primary);
    }

    setCurrentChain(items);
    setIsModified(true);
  }, [currentChain]);

  // Add provider to chain
  const addToChain = useCallback((providerName: string) => {
    if (currentChain.some(item => item.provider === providerName)) return;

    const newItem: ChainItem = {
      id: `fallback-${providerName}-${Date.now()}`,
      provider: providerName,
      weight: 20,
      isPrimary: false,
    };

    setCurrentChain(prev => [...prev, newItem]);
    setIsModified(true);
  }, [currentChain]);

  // Remove provider from chain
  const removeFromChain = useCallback((itemId: string) => {
    setCurrentChain(prev => prev.filter(item => item.id !== itemId && !item.isPrimary));
    setIsModified(true);
  }, []);

  // Update weight
  const updateWeight = useCallback((itemId: string, weight: number) => {
    setCurrentChain(prev =>
      prev.map(item =>
        item.id === itemId ? { ...item, weight } : item
      )
    );
    setIsModified(true);
  }, []);

  // Generate optimized weights based on strategy
  const optimizeWeights = useCallback((strategy: 'cost' | 'latency' | 'reliability') => {
    const updatedChain = currentChain.map(item => {
      const provider = providers.find(p => p.provider === item.provider);
      if (!provider) return item;

      let weight = 20; // Base weight

      switch (strategy) {
        case 'cost':
          // Higher weight for lower cost
          weight = Math.max(10, 100 - (provider.cost_per_1k_tokens * 10000));
          break;
        case 'latency':
          // Higher weight for lower latency
          weight = Math.max(10, 100 - (provider.avg_latency_ms / 50));
          break;
        case 'reliability':
          // Higher weight for higher success rate
          weight = provider.success_rate;
          break;
      }

      return { ...item, weight: Math.round(weight) };
    });

    // Normalize weights to sum to 100
    const totalWeight = updatedChain.reduce((sum, item) => sum + item.weight, 0);
    const normalizedChain = updatedChain.map(item => ({
      ...item,
      weight: Math.round((item.weight / totalWeight) * 100),
    }));

    setCurrentChain(normalizedChain);
    setIsModified(true);
  }, [currentChain, providers]);

  // Save chain configuration
  const saveChain = useCallback(async () => {
    if (!selectedPrimary) return;

    try {
      setIsSaving(true);
      setSaveMessage(null);

      const config: FallbackChainConfig = {
        primary_provider: selectedPrimary,
        fallback_chain: currentChain.filter(item => !item.isPrimary).map(item => item.provider),
        load_balance_weights: Object.fromEntries(
          currentChain.map(item => [item.provider, item.weight])
        ),
        routing_strategy: routingStrategy,
      };

      await onUpdateChain(selectedPrimary, config);
      setIsModified(false);
      setSaveMessage('✅ Fallback chain saved successfully!');

      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      setSaveMessage(`❌ Save failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsSaving(false);
    }
  }, [selectedPrimary, currentChain, routingStrategy, onUpdateChain]);

  // Reset to original configuration
  const resetChain = useCallback(() => {
    if (selectedPrimary && fallbackChains[selectedPrimary]) {
      const config = fallbackChains[selectedPrimary];
      const chainItems: ChainItem[] = [
        {
          id: `primary-${selectedPrimary}`,
          provider: selectedPrimary,
          weight: config.load_balance_weights[selectedPrimary] || 70,
          isPrimary: true,
        },
        ...config.fallback_chain.map((provider, index) => ({
          id: `fallback-${provider}-${index}`,
          provider,
          weight: config.load_balance_weights[provider] || 30 / config.fallback_chain.length,
          isPrimary: false,
        })),
      ];
      setCurrentChain(chainItems);
      setRoutingStrategy(config.routing_strategy);
      setIsModified(false);
    }
  }, [selectedPrimary, fallbackChains]);

  // Calculate chain statistics
  const chainStats = React.useMemo(() => {
    const totalCost = currentChain.reduce((sum, item) => {
      const provider = providers.find(p => p.provider === item.provider);
      return sum + (provider ? provider.cost_per_1k_tokens * (item.weight / 100) : 0);
    }, 0);

    const avgLatency = currentChain.reduce((sum, item) => {
      const provider = providers.find(p => p.provider === item.provider);
      return sum + (provider ? provider.avg_latency_ms * (item.weight / 100) : 0);
    }, 0);

    const avgReliability = currentChain.reduce((sum, item) => {
      const provider = providers.find(p => p.provider === item.provider);
      return sum + (provider ? provider.success_rate * (item.weight / 100) : 0);
    }, 0);

    return {
      totalCost,
      avgLatency,
      avgReliability,
    };
  }, [currentChain, providers]);

  const availableProviders = providers.filter(
    provider => !currentChain.some(item => item.provider === provider.provider)
  );

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Primary Provider Selection */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <label className="text-sm font-medium text-gray-700">Primary Provider</label>
          <Select value={selectedPrimary} onValueChange={setSelectedPrimary}>
            <SelectTrigger>
              <SelectValue placeholder="Select primary provider" />
            </SelectTrigger>
            <SelectContent>
              {providers.map((provider) => (
                <SelectItem key={provider.provider} value={provider.provider}>
                  <div className="flex items-center gap-2">
                    <div className={getProviderStatus(provider.provider).color}>
                      {getProviderStatus(provider.provider).icon}
                    </div>
                    <span className="capitalize">{provider.provider}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex-1">
          <label className="text-sm font-medium text-gray-700">Routing Strategy</label>
          <Select value={routingStrategy} onValueChange={(value) => {
            setRoutingStrategy(value);
            setIsModified(true);
          }}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {routingStrategies.map((strategy) => (
                <SelectItem key={strategy.name} value={strategy.name}>
                  {strategy.display_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Tabs defaultValue="builder" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="builder">Chain Builder</TabsTrigger>
          <TabsTrigger value="optimization">Optimization</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        {/* Chain Builder */}
        <TabsContent value="builder" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Current Chain */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Fallback Chain
                </CardTitle>
                <CardDescription>
                  Drag to reorder. Primary provider is always first.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DragDropContext onDragEnd={onDragEnd}>
                  <Droppable droppableId="chain">
                    {(provided) => (
                      <div
                        {...provided.droppableProps}
                        ref={provided.innerRef}
                        className="space-y-2"
                      >
                        {currentChain.map((item, index) => (
                          <Draggable
                            key={item.id}
                            draggableId={item.id}
                            index={index}
                            isDragDisabled={item.isPrimary}
                          >
                            {(provided, snapshot) => (
                              <div
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                                className={`p-3 border rounded-lg transition-colors ${
                                  snapshot.isDragging ? 'bg-blue-50 border-blue-300' : 'bg-white hover:bg-gray-50'
                                } ${item.isPrimary ? 'border-blue-500 bg-blue-50' : ''}`}
                              >
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-3">
                                    <div className={getProviderStatus(item.provider).color}>
                                      {getProviderStatus(item.provider).icon}
                                    </div>
                                    <div>
                                      <div className="flex items-center gap-2">
                                        <span className="font-medium capitalize">{item.provider}</span>
                                        {item.isPrimary && (
                                          <Badge variant="default" className="text-xs">
                                            Primary
                                          </Badge>
                                        )}
                                      </div>
                                      <div className="text-xs text-gray-500">
                                        {index === 0 ? 'First choice' : `Fallback ${index}`}
                                      </div>
                                    </div>
                                  </div>

                                  <div className="flex items-center gap-2">
                                    <div className="flex items-center gap-2">
                                      <Input
                                        type="number"
                                        min="1"
                                        max="100"
                                        value={item.weight}
                                        onChange={(e) => updateWeight(item.id, parseInt(e.target.value) || 0)}
                                        className="w-16 h-8 text-center"
                                      />
                                      <span className="text-xs text-gray-500">%</span>
                                    </div>

                                    {!item.isPrimary && (
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => removeFromChain(item.id)}
                                        className="h-8 w-8 p-0 text-red-500 hover:text-red-700"
                                      >
                                        <X className="h-4 w-4" />
                                      </Button>
                                    )}
                                  </div>
                                </div>
                              </div>
                            )}
                          </Draggable>
                        ))}
                        {provided.placeholder}
                      </div>
                    )}
                  </Droppable>
                </DragDropContext>
              </CardContent>
            </Card>

            {/* Available Providers */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Plus className="h-5 w-5" />
                  Available Providers
                </CardTitle>
                <CardDescription>
                  Click to add providers to your fallback chain
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {availableProviders.map((provider) => (
                    <div
                      key={provider.provider}
                      className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => addToChain(provider.provider)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={getProviderStatus(provider.provider).color}>
                            {getProviderStatus(provider.provider).icon}
                          </div>
                          <div>
                            <div className="font-medium capitalize">{provider.provider}</div>
                            <div className="text-xs text-gray-500 flex items-center gap-3">
                              <span>{provider.success_rate.toFixed(1)}% success</span>
                              <span>{provider.avg_latency_ms.toFixed(0)}ms latency</span>
                              <span>${provider.cost_per_1k_tokens.toFixed(4)}/1k tokens</span>
                            </div>
                          </div>
                        </div>
                        <Plus className="h-4 w-4 text-gray-400" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Optimization */}
        <TabsContent value="optimization" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="outline"
              onClick={() => optimizeWeights('cost')}
              className="h-auto p-4 flex flex-col items-start gap-2"
            >
              <div className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-green-600" />
                <span className="font-medium">Cost Optimize</span>
              </div>
              <p className="text-sm text-gray-600 text-left">
                Prioritize providers with lower costs per token
              </p>
            </Button>

            <Button
              variant="outline"
              onClick={() => optimizeWeights('latency')}
              className="h-auto p-4 flex flex-col items-start gap-2"
            >
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-blue-600" />
                <span className="font-medium">Speed Optimize</span>
              </div>
              <p className="text-sm text-gray-600 text-left">
                Prioritize providers with lower latency
              </p>
            </Button>

            <Button
              variant="outline"
              onClick={() => optimizeWeights('reliability')}
              className="h-auto p-4 flex flex-col items-start gap-2"
            >
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-purple-600" />
                <span className="font-medium">Reliability Optimize</span>
              </div>
              <p className="text-sm text-gray-600 text-left">
                Prioritize providers with higher success rates
              </p>
            </Button>
          </div>
        </TabsContent>

        {/* Analytics */}
        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-green-600" />
                  <div>
                    <div className="text-sm text-gray-600">Weighted Avg Cost</div>
                    <div className="text-xl font-bold">${chainStats.totalCost.toFixed(4)}</div>
                    <div className="text-xs text-gray-500">per 1K tokens</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-blue-600" />
                  <div>
                    <div className="text-sm text-gray-600">Weighted Avg Latency</div>
                    <div className="text-xl font-bold">{chainStats.avgLatency.toFixed(0)}ms</div>
                    <div className="text-xs text-gray-500">expected response time</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-purple-600" />
                  <div>
                    <div className="text-sm text-gray-600">Weighted Reliability</div>
                    <div className="text-xl font-bold">{chainStats.avgReliability.toFixed(1)}%</div>
                    <div className="text-xs text-gray-500">expected success rate</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Save Message */}
      {saveMessage && (
        <Alert>
          <AlertDescription>{saveMessage}</AlertDescription>
        </Alert>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isModified && (
            <Badge variant="secondary" className="text-orange-600">
              Unsaved Changes
            </Badge>
          )}
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={resetChain}
            disabled={!isModified}
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>

          <Button
            onClick={saveChain}
            disabled={!isModified || isSaving}
          >
            {isSaving ? (
              <>
                <Activity className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Chain
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};
