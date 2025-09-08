# Implementation Roadmap (Cross-Referenced)

## Overview
- Dashboards: 11
- Chat components: 19
- Realtime totals: {'WebSocket': 142, 'EventSource': 2, 'SSE': 19, 'socket.io': 0, 'io(': 6}
- API totals: {'fetch': 64, 'axios': 0}

## Dashboards: API & Realtime Heatmap
- `agent-ui/src/components/dashboards/ProjectManagementDashboard.tsx` — RT: 7, API: 7
- `agent-ui/src/components/dashboards/ClientHealthDashboard.tsx` — RT: 7, API: 6
- `agent-ui/src/components/dashboards/SalesPerformanceDashboard.tsx` — RT: 7, API: 5
- `agent-ui/src/components/sophia/PayReadyDashboard.tsx` — RT: 6, API: 1
- `agent-ui/src/components/infrastructure/InfraDashboard.tsx` — RT: 0, API: 7
- `agent-ui/src/components/analytics/CostDashboard.tsx` — RT: 0, API: 3
- `agent-ui/src/components/llm-control/ModelControlDashboard.tsx` — RT: 0, API: 2
- `agent-ui/src/app/(sophia)/dashboard/page.tsx` — RT: 0, API: 0
- `agent-ui/src/components/model-registry/ModelRegistryDashboard.tsx` — RT: 0, API: 0
- `agent-ui/src/components/project-management/MobileProjectDashboard.tsx` — RT: 0, API: 0
- `agent-ui/src/components/prompt-library/PromptLibraryDashboard.tsx` — RT: 0, API: 0

## Chat Components: API & Realtime Heatmap
- `agent-ui/src/components/playground/ChatArea/Messages/Multimedia/Audios/Audios.tsx` — RT: 2, API: 0
- `agent-ui/src/components/playground/ChatArea/Messages/Multimedia/Videos/Videos.tsx` — RT: 0, API: 1
- `agent-ui/src/components/playground/ChatArea/ChatArea.tsx` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/ChatInput/ChatInput.tsx` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/ChatInput/index.ts` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/MessageArea.tsx` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/Messages/AgentThinkingLoader.tsx` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/Messages/ChatBlankState.tsx` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/Messages/MessageItem.tsx` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/Messages/Messages.tsx` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/Messages/Multimedia/Audios/index.ts` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/Messages/Multimedia/Images/Images.tsx` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/Messages/Multimedia/Images/index.ts` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/Messages/Multimedia/Videos/index.ts` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/Messages/index.ts` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/ScrollToBottom.tsx` — RT: 0, API: 0
- `agent-ui/src/components/playground/ChatArea/index.ts` — RT: 0, API: 0
- `agent-ui/src/components/playground/Sidebar/NewChatButton.tsx` — RT: 0, API: 0
- `agent-ui/src/hooks/useChatActions.ts` — RT: 0, API: 0

## Week-by-Week Actions
- Weeks 1–2: Implement `lib/realtime/RealtimeManager.ts` and `lib/api/client.ts`; wire into top 5 realtime/API hotspots.
- Weeks 3–4: Extract shared widgets from highest-RT dashboards first (see heatmap).
- Weeks 5–6: Build `CommandCenter` layout and route aggregation; replace per-dashboard state with store slices.
- Week 7: Unify ChatArea + stream display using `useAIStreamHandler` and RealtimeManager.
- Week 8: Harmonize MCP/Swarm UIs and endpoint selectors.
- Week 9: Integrate analytics and model registry views with unified widgets.
- Week 10: Add tests and Storybook stories for widgets and managers.
- Week 11: Toggle-based rollout; monitor RT/API error rates.
