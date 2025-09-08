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
  updateLatency: (category: string, p95: number) => void
  setBudgetState: (vkEnv: string, used: number, softCap: number, hardCap: number) => void
}

export type UnifiedState = ChatState & SwarmState & MetricsState

// ---- Slices ----
const chatSlice = (set: any): ChatState => ({
  messages: [],
  sending: false,
  addMessage: (m) => set((s: ChatState) => ({ messages: [...s.messages, m] })),
  setSending: (v) => set({ sending: v }),
  resetChat: () => set({ messages: [], sending: false }),
})

const swarmSlice = (set: any): SwarmState => ({
  tasks: [],
  status: 'idle',
  enqueue: (t) => set((s: SwarmState) => ({ tasks: [...s.tasks, t] })),
  updateTask: (id, patch) => set((s: SwarmState) => ({
    tasks: s.tasks.map((t) => (t.id === id ? { ...t, ...patch } : t)),
  })),
  setStatus: (s) => set({ status: s }),
})

const metricsSlice = (set: any): MetricsState => ({
  p95LatencyMs: {},
  vkBudgetState: {},
  updateLatency: (category, p95) => set((s: MetricsState) => ({
    p95LatencyMs: { ...s.p95LatencyMs, [category]: p95 },
  })),
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

