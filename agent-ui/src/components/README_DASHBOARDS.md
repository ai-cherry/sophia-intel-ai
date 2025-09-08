# SuperOrchestrator Dashboard Documentation

## IMPORTANT: Which Dashboard to Use

### ✅ USE THIS: UnifiedSuperDashboard.tsx

- **Location**: `agent-ui/src/components/UnifiedSuperDashboard.tsx`
- **Lines**: 1102
- **Status**: ACTIVE - This is the primary dashboard
- **Features**:
  - 8 comprehensive tabs (Overview, Systems, Swarms, Analytics, Models, Infrastructure, Monitoring, History)
  - Natural language command interface
  - Full personality integration
  - Cost tracking and analytics
  - Model management
  - Infrastructure monitoring
  - WebSocket port: 8000 (correct)

### ⚠️ DEPRECATED: SuperOrchestratorDashboard.tsx

- **Location**: `agent-ui/src/components/SuperOrchestratorDashboard.tsx`
- **Lines**: 483
- **Status**: DEPRECATED - Keep for reference only
- **Note**: Simpler implementation, uses incorrect WebSocket port (8006)
- **Action**: Consider removing after confirming UnifiedSuperDashboard works

## How to Use

```tsx
// In your main app or page component:
import UnifiedSuperDashboard from '@/components/UnifiedSuperDashboard';

function App() {
  return <UnifiedSuperDashboard />;
}
```

## Backend Files

The dashboard connects to these backend components:

- `app/core/super_orchestrator.py` - Main orchestrator engine
- `app/core/orchestrator_personality.py` - Personality system
- `app/api/super_orchestrator_router.py` - API endpoints
- `app/core/orchestrator_enhancements.py` - Universal registry and monitoring

## WebSocket Configuration

- Endpoint: `ws://localhost:8000/ws/orchestrator`
- Backend port: 8000
- Frontend port: 3000 (Next.js dev server)

## Customization Based on User Preferences

This dashboard was customized based on these preferences:

- Natural language control with visual support
- Swarm Intelligence → Task Progress → System Health → Cost visibility priorities
- AI-suggested but customizable micro-swarms
- AI Insights monitoring mode
- Conversational assistant with collaborative confirmations
- Memory System Browser + Swarm Replay/History features
- Clean/Rich visual balance with dark theme
- Enthusiastic personality that curses a little and pushes back on risky commands
