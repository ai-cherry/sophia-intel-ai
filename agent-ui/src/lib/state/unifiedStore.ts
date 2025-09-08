/*
  Unified Zustand store
  - Compose slices: chat, swarm, metrics
  - Non-breaking; migrate components incrementally from existing store.ts
*/
import { create } from 'zustand'

// ---- Types ----
export interface ChatMessage { id: string; role: 'user' | 'assistant' | 'system'; content: string; ts: number }
export interface ChatState {
  messages: ChatMessage[]
  sending: boolean
  addMessage: (m: ChatMessage) => void
  setSending: (v: boolean) => void
  resetChat: () => void
}

export interface SwarmTask { id: string; title: string; status: 'queued' | 'running' | 'done' | 'error' }
export interface SwarmState {
  tasks: SwarmTask[]
  status: 'idle' | 'active'
  enqueue: (t: SwarmTask) => void
  updateTask: (id: string, patch: Partial<SwarmTask>) => void
  setStatus: (s: SwarmState['status']) => void
}

export interface MetricsState {
  p95LatencyMs: Record<string, number> // by route category
  vkBudgetState: Record<string, { used: number; softCap: number; hardCap: number }>
  updateLatency: (category: string, sampleMs: number) => void
  setBudgetState: (vkEnv: string, used: number, softCap: number, hardCap: number) => void
}

export type UnifiedState = ChatState & SwarmState & MetricsState

// ---- Slices ----
const chatSlice = (set: unknown): ChatState => ({
  messages: [],
  sending: false,
  addMessage: (m) => set((s: ChatState) => ({ messages: [...s.messages, m] })),
  setSending: (v) => set({ sending: v }),
  resetChat: () => set({ messages: [], sending: false }),
})

const swarmSlice = (set: unknown): SwarmState => ({
  tasks: [],
  status: 'idle',
  enqueue: (t) => set((s: SwarmState) => ({ tasks: [...s.tasks, t] })),
  updateTask: (id, patch) => set((s: SwarmState) => ({
    tasks: s.tasks.map((t) => (t.id === id ? { ...t, ...patch } : t)),
  })),
  setStatus: (s) => set({ status: s }),
})

const __latencyHistory: Record<string, number[]> = {};

function computeP95(samples: number[]): number {
  if (!samples.length) return 0;
  const arr = [...samples].sort((a, b) => a - b);
  const idx = Math.min(arr.length - 1, Math.floor(0.95 * (arr.length - 1)));
  return Math.round(arr[idx]);
}

const metricsSlice = (set: unknown): MetricsState => ({
  p95LatencyMs: {},
  vkBudgetState: {},
  updateLatency: (category, sampleMs) => set((s: MetricsState) => {
    const list = __latencyHistory[category] || [];
    list.push(sampleMs);
    if (list.length > 50) list.shift();
    __latencyHistory[category] = list;
    const p95 = computeP95(list);
    return { p95LatencyMs: { ...s.p95LatencyMs, [category]: p95 } } as any;
  }),
  setBudgetState: (vkEnv, used, softCap, hardCap) => set((s: MetricsState) => ({
    vkBudgetState: { ...s.vkBudgetState, [vkEnv]: { used, softCap, hardCap } },
  })),
})

// ---- Store ----
export const useUnifiedStore = create<UnifiedState>()((set) => ({
  ...chatSlice(set),
  ...swarmSlice(set),
  ...metricsSlice(set),
}))