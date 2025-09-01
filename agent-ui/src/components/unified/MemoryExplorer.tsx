/**
 * Memory Explorer Component
 * Interactive memory visualization with graph view and context suggestions
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Database,
  Search,
  Filter,
  Eye,
  EyeOff,
  GitBranch,
  Link,
  Clock,
  Tag,
  Sparkles,
  ChevronRight,
  ChevronDown
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';

interface MemoryItem {
  id: string;
  content: string;
  metadata: {
    type?: string;
    session_id?: string;
    timestamp?: string;
    tags?: string[];
    [key: string]: any;
  };
  similarity?: number;
  coherence?: number;
}

interface MemoryGraph {
  nodes: Array<{
    id: string;
    label: string;
    type: string;
  }>;
  edges: Array<{
    from: string;
    to: string;
    weight: number;
  }>;
}

interface MemoryContextData {
  relevant_memories: MemoryItem[];
  suggested_memories: MemoryItem[];
  memory_graph: MemoryGraph;
  coherence_score: number;
}

interface MemoryExplorerProps {
  contextData?: MemoryContextData;
  onMemorySelect?: (memory: MemoryItem) => void;
  onSearch?: (query: string) => void;
  onSuggest?: () => void;
}

export const MemoryExplorer: React.FC<MemoryExplorerProps> = ({
  contextData,
  onMemorySelect,
  onSearch,
  onSuggest
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMemory, setSelectedMemory] = useState<MemoryItem | null>(null);
  const [expandedMemories, setExpandedMemories] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'list' | 'graph' | 'timeline'>('list');
  const [showSuggested, setShowSuggested] = useState(true);

  const handleSearch = useCallback(() => {
    if (searchQuery && onSearch) {
      onSearch(searchQuery);
    }
  }, [searchQuery, onSearch]);

  const toggleMemoryExpansion = (memoryId: string) => {
    setExpandedMemories(prev => {
      const next = new Set(prev);
      if (next.has(memoryId)) {
        next.delete(memoryId);
      } else {
        next.add(memoryId);
      }
      return next;
    });
  };

  const renderMemoryItem = (memory: MemoryItem, index: number) => {
    const isExpanded = expandedMemories.has(memory.id);
    const isSelected = selectedMemory?.id === memory.id;

    return (
      <motion.div
        key={memory.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.05 }}
        className={`border rounded-lg p-3 cursor-pointer transition-all ${
          isSelected ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700'
        }`}
        onClick={() => {
          setSelectedMemory(memory);
          onMemorySelect?.(memory);
        }}
      >
        {/* Memory Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-2 flex-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleMemoryExpansion(memory.id);
              }}
              className="mt-1"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                {memory.metadata.type && (
                  <Badge variant="outline" className="text-xs">
                    {memory.metadata.type}
                  </Badge>
                )}
                {memory.similarity && (
                  <Badge variant="secondary" className="text-xs">
                    {Math.round(memory.similarity * 100)}% match
                  </Badge>
                )}
                {memory.coherence && (
                  <Badge variant="secondary" className="text-xs">
                    <Sparkles className="w-3 h-3 mr-1" />
                    {Math.round(memory.coherence * 100)}%
                  </Badge>
                )}
              </div>
              
              <div className="text-sm">
                {isExpanded ? (
                  <div className="whitespace-pre-wrap">{memory.content}</div>
                ) : (
                  <div className="truncate">{memory.content}</div>
                )}
              </div>
              
              {memory.metadata.tags && memory.metadata.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {memory.metadata.tags.map((tag) => (
                    <Badge key={tag} variant="outline" className="text-xs">
                      <Tag className="w-3 h-3 mr-1" />
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          {memory.metadata.timestamp && (
            <div className="text-xs text-gray-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(memory.metadata.timestamp).toLocaleDateString()}
            </div>
          )}
        </div>
        
        {/* Expanded Metadata */}
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700"
          >
            <div className="text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-500">ID:</span>
                <span className="font-mono">{memory.id}</span>
              </div>
              {memory.metadata.session_id && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Session:</span>
                  <span className="font-mono">{memory.metadata.session_id}</span>
                </div>
              )}
              {Object.entries(memory.metadata).map(([key, value]) => {
                if (['type', 'timestamp', 'tags', 'session_id'].includes(key)) return null;
                return (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-500">{key}:</span>
                    <span className="truncate ml-2">{JSON.stringify(value)}</span>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </motion.div>
    );
  };

  const renderGraphView = () => {
    if (!contextData?.memory_graph) {
      return (
        <div className="flex items-center justify-center h-64 text-gray-500">
          No memory graph available
        </div>
      );
    }

    // Simple graph visualization (would use D3.js or React Flow in production)
    return (
      <div className="relative h-64 overflow-hidden">
        <svg className="w-full h-full">
          {/* Render edges */}
          {contextData.memory_graph.edges.map((edge, index) => {
            const fromNode = contextData.memory_graph.nodes.find(n => n.id === edge.from);
            const toNode = contextData.memory_graph.nodes.find(n => n.id === edge.to);
            if (!fromNode || !toNode) return null;
            
            const fromIndex = contextData.memory_graph.nodes.indexOf(fromNode);
            const toIndex = contextData.memory_graph.nodes.indexOf(toNode);
            const x1 = 50 + fromIndex * 100;
            const y1 = 100;
            const x2 = 50 + toIndex * 100;
            const y2 = 100;
            
            return (
              <line
                key={index}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="gray"
                strokeWidth={edge.weight * 2}
                opacity={0.5}
              />
            );
          })}
          
          {/* Render nodes */}
          {contextData.memory_graph.nodes.map((node, index) => (
            <g key={node.id} transform={`translate(${50 + index * 100}, 100)`}>
              <circle
                r="20"
                fill="white"
                stroke="gray"
                strokeWidth="2"
                className="cursor-pointer hover:fill-blue-100"
              />
              <text
                textAnchor="middle"
                y="5"
                className="text-xs fill-gray-700"
              >
                {node.label.substring(0, 10)}
              </text>
            </g>
          ))}
        </svg>
      </div>
    );
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            <h3 className="font-semibold">Memory Context</h3>
            {contextData && (
              <Badge variant="outline">
                {contextData.relevant_memories.length + contextData.suggested_memories.length} items
              </Badge>
            )}
          </div>
          
          {contextData && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">Coherence:</span>
              <Badge variant="secondary">
                {Math.round(contextData.coherence_score * 100)}%
              </Badge>
            </div>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Search Bar */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search memories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="pl-9"
            />
          </div>
          <Button onClick={handleSearch} size="sm">
            Search
          </Button>
          {onSuggest && (
            <Button onClick={onSuggest} size="sm" variant="outline">
              <Sparkles className="w-4 h-4 mr-1" />
              Suggest
            </Button>
          )}
        </div>
        
        {/* View Mode Tabs */}
        <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="list">List</TabsTrigger>
            <TabsTrigger value="graph">Graph</TabsTrigger>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
          </TabsList>
          
          <TabsContent value="list" className="space-y-4">
            {/* Toggle Suggested Memories */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Suggested Memories</span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShowSuggested(!showSuggested)}
              >
                {showSuggested ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </Button>
            </div>
            
            {/* Memory List */}
            <ScrollArea className="h-96">
              <div className="space-y-2">
                {/* Relevant Memories */}
                {contextData?.relevant_memories.map((memory, index) =>
                  renderMemoryItem(memory, index)
                )}
                
                {/* Suggested Memories */}
                {showSuggested && contextData?.suggested_memories.length > 0 && (
                  <>
                    <div className="text-sm font-medium text-gray-500 mt-4">
                      Suggested
                    </div>
                    {contextData.suggested_memories.map((memory, index) =>
                      renderMemoryItem(memory, index + (contextData.relevant_memories?.length || 0))
                    )}
                  </>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="graph">
            {renderGraphView()}
          </TabsContent>
          
          <TabsContent value="timeline">
            <div className="text-center text-gray-500 py-8">
              Timeline view coming soon
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};