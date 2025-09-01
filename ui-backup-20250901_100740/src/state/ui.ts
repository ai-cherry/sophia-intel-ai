import { create } from 'zustand';
import { Team, Workflow, StreamResponse } from '@/lib/types';
import { getEndpoint, setEndpoint as saveEndpoint } from '@/lib/endpoint';

interface UIState {
  // Endpoint
  endpoint: string;
  isConnected: boolean;
  setEndpoint: (url: string) => void;
  setConnected: (connected: boolean) => void;
  
  // Teams & Workflows
  teams: Team[];
  workflows: Workflow[];
  selectedTeam: Team | null;
  selectedWorkflow: Workflow | null;
  setTeams: (teams: Team[]) => void;
  setWorkflows: (workflows: Workflow[]) => void;
  selectTeam: (team: Team | null) => void;
  selectWorkflow: (workflow: Workflow | null) => void;
  
  // Streaming
  isStreaming: boolean;
  streamContent: string;
  lastResponse: StreamResponse | null;
  setStreaming: (streaming: boolean) => void;
  appendContent: (content: string) => void;
  clearContent: () => void;
  setLastResponse: (response: StreamResponse | null) => void;
  
  // Pool & priority
  pool: 'fast' | 'heavy' | 'balanced';
  priority: 'low' | 'medium' | 'high' | 'critical';
  setPool: (pool: 'fast' | 'heavy' | 'balanced') => void;
  setPriority: (priority: 'low' | 'medium' | 'high' | 'critical') => void;
}

export const useUIStore = create<UIState>((set) => ({
  // Endpoint
  endpoint: getEndpoint(),
  isConnected: false,
  setEndpoint: (url) => {
    saveEndpoint(url);
    set({ endpoint: url, isConnected: false });
  },
  setConnected: (connected) => set({ isConnected: connected }),
  
  // Teams & Workflows
  teams: [],
  workflows: [],
  selectedTeam: null,
  selectedWorkflow: null,
  setTeams: (teams) => set({ teams }),
  setWorkflows: (workflows) => set({ workflows }),
  selectTeam: (team) => set({ selectedTeam: team }),
  selectWorkflow: (workflow) => set({ selectedWorkflow: workflow }),
  
  // Streaming
  isStreaming: false,
  streamContent: '',
  lastResponse: null,
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  appendContent: (content) => set((state) => ({
    streamContent: state.streamContent + content
  })),
  clearContent: () => set({ streamContent: '', lastResponse: null }),
  setLastResponse: (response) => set({ lastResponse: response }),
  
  // Pool & priority
  pool: 'balanced',
  priority: 'medium',
  setPool: (pool) => set({ pool }),
  setPriority: (priority) => set({ priority }),
}));