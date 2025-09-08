# SOPHIA UI Unification Report

## Summary
- Files scanned: 139
- Dashboards: 11
- Chat components: 19
- API calls: {'fetch': 64, 'axios': 0}
- State hooks: {'useState': 327, 'useReducer': 0, 'useContext': 2, 'zustand': 2, 'redux': 0}
- Realtime: {'WebSocket': 142, 'EventSource': 2, 'SSE': 19, 'socket.io': 0, 'io(': 6}
- Charts: {'recharts': 3}

## Dashboards
- `agent-ui/src/app/(sophia)/dashboard/page.tsx`
- `agent-ui/src/components/analytics/CostDashboard.tsx`
- `agent-ui/src/components/dashboards/ClientHealthDashboard.tsx`
- `agent-ui/src/components/dashboards/ProjectManagementDashboard.tsx`
- `agent-ui/src/components/dashboards/SalesPerformanceDashboard.tsx`
- `agent-ui/src/components/infrastructure/InfraDashboard.tsx`
- `agent-ui/src/components/llm-control/ModelControlDashboard.tsx`
- `agent-ui/src/components/model-registry/ModelRegistryDashboard.tsx`
- `agent-ui/src/components/project-management/MobileProjectDashboard.tsx`
- `agent-ui/src/components/prompt-library/PromptLibraryDashboard.tsx`
- `agent-ui/src/components/sophia/PayReadyDashboard.tsx`

## Chat Components
- `agent-ui/src/components/playground/ChatArea/ChatArea.tsx`
- `agent-ui/src/components/playground/ChatArea/ChatInput/ChatInput.tsx`
- `agent-ui/src/components/playground/ChatArea/ChatInput/index.ts`
- `agent-ui/src/components/playground/ChatArea/MessageArea.tsx`
- `agent-ui/src/components/playground/ChatArea/Messages/AgentThinkingLoader.tsx`
- `agent-ui/src/components/playground/ChatArea/Messages/ChatBlankState.tsx`
- `agent-ui/src/components/playground/ChatArea/Messages/MessageItem.tsx`
- `agent-ui/src/components/playground/ChatArea/Messages/Messages.tsx`
- `agent-ui/src/components/playground/ChatArea/Messages/Multimedia/Audios/Audios.tsx`
- `agent-ui/src/components/playground/ChatArea/Messages/Multimedia/Audios/index.ts`
- `agent-ui/src/components/playground/ChatArea/Messages/Multimedia/Images/Images.tsx`
- `agent-ui/src/components/playground/ChatArea/Messages/Multimedia/Images/index.ts`
- `agent-ui/src/components/playground/ChatArea/Messages/Multimedia/Videos/Videos.tsx`
- `agent-ui/src/components/playground/ChatArea/Messages/Multimedia/Videos/index.ts`
- `agent-ui/src/components/playground/ChatArea/Messages/index.ts`
- `agent-ui/src/components/playground/ChatArea/ScrollToBottom.tsx`
- `agent-ui/src/components/playground/ChatArea/index.ts`
- `agent-ui/src/components/playground/Sidebar/NewChatButton.tsx`
- `agent-ui/src/hooks/useChatActions.ts`

## Top Files

### api_calls
- `agent-ui/src/hooks/useModelRegistry.ts` — 9
- `agent-ui/src/api/playground.ts` — 9
- `agent-ui/src/components/dashboards/ProjectManagementDashboard.tsx` — 7
- `agent-ui/src/components/infrastructure/InfraDashboard.tsx` — 7
- `agent-ui/src/components/dashboards/ClientHealthDashboard.tsx` — 6
- `agent-ui/src/components/dashboards/SalesPerformanceDashboard.tsx` — 5
- `agent-ui/src/components/analytics/CostDashboard.tsx` — 3
- `agent-ui/src/hooks/useMCPStatus.ts` — 3
- `agent-ui/src/app/(sophia)/chat/page.tsx` — 2
- `agent-ui/src/components/llm-control/ModelControlDashboard.tsx` — 2

### state_hooks
- `agent-ui/src/components/prompt-library/PromptLibraryDashboard.tsx` — 17
- `agent-ui/src/components/dashboards/ProjectManagementDashboard.tsx` — 16
- `agent-ui/src/components/dashboards/ClientHealthDashboard.tsx` — 15
- `agent-ui/src/components/dashboards/SalesPerformanceDashboard.tsx` — 15
- `agent-ui/src/hooks/useOrchestratorCoordination.ts` — 12
- `agent-ui/src/hooks/useModelRegistry.ts` — 12
- `agent-ui/src/components/swarm/TeamWorkflowPanel.tsx` — 11
- `agent-ui/src/components/sophia/PayReadyDashboard.tsx` — 10
- `agent-ui/src/app/(sophia)/chat/page.tsx` — 9
- `agent-ui/src/components/swarm-builder/SwarmTemplateSelector.tsx` — 9

### realtime
- `agent-ui/src/hooks/useAGUIEvents.ts` — 39
- `agent-ui/src/hooks/useSwarmTemplates.ts` — 23
- `agent-ui/src/hooks/useModelRegistry.ts` — 18
- `agent-ui/src/hooks/useMCPStatus.ts` — 17
- `agent-ui/src/hooks/usePromptLibrary.ts` — 17
- `agent-ui/src/hooks/useOrchestratorCoordination.ts` — 15
- `agent-ui/src/components/dashboards/ClientHealthDashboard.tsx` — 7
- `agent-ui/src/components/dashboards/SalesPerformanceDashboard.tsx` — 7
- `agent-ui/src/components/dashboards/ProjectManagementDashboard.tsx` — 7
- `agent-ui/src/components/sophia/PayReadyDashboard.tsx` — 6

### charts
- `agent-ui/src/components/prompt-library/PromptLibraryDashboard.tsx` — 1
- `agent-ui/src/components/infrastructure/InfraDashboard.tsx` — 1
- `agent-ui/src/components/analytics/CostDashboard.tsx` — 1
