'use client';

import React, { useState } from 'react';
import { Search, Plus, Trash2, Database } from 'lucide-react';

interface Memory {
  id: string;
  content: string;
  metadata: Record<string, any>;
  timestamp: Date;
  similarity?: number;
}

interface MemoryExplorerProps {
  searchEndpoint: string;
  writeEndpoint: string;
  deleteEndpoint: string;
  expanded?: boolean;
}

export const MemoryExplorer: React.FC<MemoryExplorerProps> = ({
  searchEndpoint,
  writeEndpoint,
  deleteEndpoint,
  expanded = false
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(false);
  const [newMemory, setNewMemory] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  const searchMemories = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(searchEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery })
      });
      
      if (response.ok) {
        const data = await response.json();
        setMemories(data.results || []);
      }
    } catch (error) {
      console.error('Failed to search memories:', error);
    } finally {
      setLoading(false);
    }
  };

  const addMemory = async () => {
    if (!newMemory.trim()) return;
    
    try {
      const response = await fetch(writeEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          content: newMemory,
          metadata: {
            source: 'manual',
            timestamp: new Date().toISOString()
          }
        })
      });
      
      if (response.ok) {
        setNewMemory('');
        setShowAddForm(false);
        searchMemories(); // Refresh results
      }
    } catch (error) {
      console.error('Failed to add memory:', error);
    }
  };

  const deleteMemory = async (id: string) => {
    try {
      const response = await fetch(deleteEndpoint, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      
      if (response.ok) {
        setMemories(memories.filter(m => m.id !== id));
      }
    } catch (error) {
      console.error('Failed to delete memory:', error);
    }
  };

  return (
    <div className={`space-y-4 ${expanded ? 'h-full flex flex-col' : ''}`}>
      {/* Search Bar */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/50" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && searchMemories()}
            placeholder="Search memories..."
            className="w-full bg-white/10 border border-white/20 rounded-lg pl-10 pr-4 py-2 text-white placeholder-white/50 focus:outline-none focus:border-[#00e0ff] transition-colors"
          />
        </div>
        <button
          onClick={searchMemories}
          disabled={loading}
          className="px-4 py-2 bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Search
        </button>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
          title="Add Memory"
        >
          <Plus className="w-5 h-5" />
        </button>
      </div>

      {/* Add Memory Form */}
      {showAddForm && (
        <div className="bg-white/10 rounded-lg p-4 space-y-3">
          <textarea
            value={newMemory}
            onChange={(e) => setNewMemory(e.target.value)}
            placeholder="Enter new memory content..."
            rows={3}
            className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-white/50 focus:outline-none focus:border-[#00e0ff] transition-colors resize-none"
          />
          <div className="flex gap-2">
            <button
              onClick={addMemory}
              className="flex-1 bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] text-white rounded-lg px-4 py-2 hover:opacity-90 transition-opacity"
            >
              Add to Memory
            </button>
            <button
              onClick={() => {
                setShowAddForm(false);
                setNewMemory('');
              }}
              className="px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Results */}
      <div className={`space-y-3 ${expanded ? 'flex-1 overflow-y-auto' : 'max-h-96 overflow-y-auto'}`}>
        {loading && (
          <div className="text-center py-8">
            <Database className="w-8 h-8 mx-auto mb-2 animate-pulse" />
            <p className="text-white/50">Searching memories...</p>
          </div>
        )}
        
        {!loading && memories.length === 0 && searchQuery && (
          <div className="text-center py-8 text-white/50">
            <Database className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No memories found</p>
          </div>
        )}
        
        {memories.map((memory) => (
          <div
            key={memory.id}
            className="bg-white/5 rounded-lg p-3 hover:bg-white/10 transition-colors group"
          >
            <div className="flex items-start justify-between mb-2">
              <p className="text-sm flex-1">{memory.content}</p>
              <button
                onClick={() => deleteMemory(memory.id)}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-white/10 rounded transition-all"
                title="Delete"
              >
                <Trash2 className="w-4 h-4 text-red-400" />
              </button>
            </div>
            
            {memory.similarity !== undefined && (
              <div className="flex items-center gap-2 text-xs text-white/50">
                <span>Similarity:</span>
                <div className="flex-1 bg-white/10 rounded-full h-1">
                  <div
                    className="bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] h-1 rounded-full"
                    style={{ width: `${memory.similarity * 100}%` }}
                  />
                </div>
                <span className="font-mono">{(memory.similarity * 100).toFixed(1)}%</span>
              </div>
            )}
            
            <div className="mt-2 text-xs text-white/50">
              {new Date(memory.timestamp).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};