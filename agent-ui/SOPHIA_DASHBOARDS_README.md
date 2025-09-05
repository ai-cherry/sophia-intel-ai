# Sophia Intelligence Dashboards

A comprehensive React/TypeScript implementation of AI-powered business intelligence dashboards with mythology-themed specialized agents.

## 🏛️ Dashboard Overview

### 🌟 Unified Intelligence Hub (`/sophia`)
- **Central command center** for all AI intelligence modules
- **Real-time system health** monitoring and quick stats
- **Seamless navigation** between specialized dashboards
- **Feature showcase** and system architecture overview

### ⚡ Hermes - Sales Performance Dashboard
**Mythology**: Hermes, messenger of the gods and patron of merchants
- **Individual rep performance** cards with real-time metrics
- **Pipeline velocity** charts and conversion analytics  
- **Gong call analysis** with sentiment scoring and coaching insights
- **Red/Yellow/Green** health indicators for performance tracking
- **Voice-enabled coaching** recommendations and call playback

**Key Features**:
- Real-time WebSocket updates for sales metrics
- Gong integration for call analysis and transcription
- AI-powered coaching alerts and recommendations
- Interactive performance trend visualization
- Voice commands for hands-free operation

### 💚 Asclepius - Client Health Dashboard
**Mythology**: Asclepius, Greek god of medicine and healing
- **Client health scoring** with comprehensive risk assessment
- **Recovery metrics** visualization and intervention tracking
- **At-risk account alerts** with automated escalation
- **Expansion opportunity** identification and value projection
- **Stoplight indicators** for immediate status recognition

**Key Features**:
- AI-powered health score calculation
- Churn prediction and prevention workflows
- Expansion opportunity detection
- Recovery plan generation and tracking
- Real-time client risk monitoring

### 🧠 Athena - Project Management Dashboard
**Mythology**: Athena, goddess of wisdom, warfare, and strategy
- **Cross-platform project** status (Linear, Asana, Airtable)
- **Team alignment** visualization and communication health
- **Bottleneck identification** with automated resolution suggestions
- **Sprint progress** tracking with burndown analytics
- **Communication health** metrics and collaboration scoring

**Key Features**:
- Multi-platform synchronization (Linear, Asana, Airtable, GitHub, Jira)
- Real-time blocker detection and resolution tracking
- Team workload balancing and capacity planning
- Communication pattern analysis
- Cross-project dependency mapping

### 💬 Unified Chat Orchestration
**Advanced conversational AI** with context-aware agent routing
- **Natural language** interface with intent recognition
- **Voice input/output** integration with ElevenLabs
- **Smart agent routing** based on context and expertise
- **Context preservation** across dashboard switches
- **Multi-modal interaction** (text, voice, visual)

**Key Features**:
- ElevenLabs voice integration for natural conversations
- Context-aware agent switching and recommendations
- Real-time transcription and sentiment analysis
- Dashboard-specific command processing
- Conversation history and export capabilities

## 🛠️ Technical Implementation

### Frontend Architecture
- **React 18** with TypeScript for type safety
- **Next.js 15** for SSR and optimal performance
- **Tailwind CSS** for consistent design system
- **Shadcn/ui** components for professional UI elements
- **Lucide React** icons for consistent iconography

### Real-time Features
- **WebSocket connections** for live data streaming
- **Optimistic updates** for immediate user feedback
- **Automatic reconnection** with exponential backoff
- **Real-time collaboration** indicators

### Voice Integration
- **ElevenLabs API** for high-quality speech synthesis
- **Web Speech API** for voice recognition
- **Audio processing** with noise suppression
- **Push-to-talk** and voice activation modes

### State Management
- **React Hooks** for local component state
- **Context API** for global application state
- **WebSocket state** synchronization
- **Persistent preferences** with localStorage

### Data Visualization
- **Custom progress** indicators and health meters
- **Interactive charts** with hover states
- **Real-time metric** updates
- **Responsive grid** layouts for all screen sizes

## 🔧 Configuration

### Environment Setup
```typescript
// Environment variables needed:
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000
NEXT_PUBLIC_ELEVENLABS_API_KEY=your_api_key
NEXT_PUBLIC_ELEVENLABS_DEFAULT_VOICE_ID=rachel
NEXT_PUBLIC_VOICE_ENABLED=true
NEXT_PUBLIC_REALTIME_UPDATES=true
```

### API Endpoints Expected
```
/api/sales/reps - Sales representative data
/api/sales/gong-calls - Call recordings and analysis
/api/sales/team-metrics - Team performance metrics
/api/clients/health - Client health scores and metrics
/api/clients/recovery-plans - Churn prevention plans
/api/projects - Project management data
/api/projects/sync-status - Cross-platform sync status
/api/voice/process - Voice processing and transcription
/api/agents/available - Available AI agents
```

### WebSocket Endpoints
```
/ws/sales-hermes - Sales performance updates
/ws/client-health-asclepius - Client health monitoring
/ws/project-mgmt-athena - Project management updates
/ws/unified-chat - Chat orchestration
```

## 🎨 Design System

### Mythology-Based Themes
- **Hermes**: Blue/Purple gradient (messenger, commerce)
- **Asclepius**: Emerald/Teal gradient (healing, health)
- **Athena**: Purple/Pink gradient (wisdom, strategy)
- **Unified**: Indigo/Purple gradient (integration, intelligence)

### Responsive Design
- **Mobile-first** approach with progressive enhancement
- **Tablet optimizations** for field usage
- **Desktop experience** with multiple monitors support
- **High-DPI** support for crisp visuals

## 🚀 Usage

### Navigation
1. Start at the **Sophia Hub** (`/sophia`) for system overview
2. Click any **intelligence module** to enter specialized dashboard
3. Use the **quick navigation bar** to switch between dashboards
4. Access **unified chat** from any dashboard context

### Voice Commands
- **"Show me today's sales performance"** → Opens Hermes dashboard
- **"What clients need attention?"** → Opens Asclepius with at-risk filter
- **"Are there any project blockers?"** → Opens Athena blockers view
- **"Switch to [agent name]"** → Changes active AI agent

### Real-time Features
- **Auto-refresh** every 30 seconds for critical metrics
- **Live notifications** for alerts and status changes
- **Instant updates** when data changes on backend
- **Connection status** indicators for reliability

## 🔮 Future Enhancements

### AI Capabilities
1. **Predictive analytics** for sales forecasting
2. **Automated insight** generation and recommendations
3. **Natural language queries** for complex data exploration
4. **Multi-agent collaboration** for complex problem solving

### Integration Ideas
1. **Calendar integration** for meeting scheduling
2. **Email automation** for follow-up workflows
3. **Slack/Teams** notifications for critical alerts
4. **Mobile app** for field access and push notifications

### Advanced Features
1. **Custom dashboard** creation with drag-and-drop
2. **A/B testing** framework for dashboard optimization
3. **Advanced permissions** and role-based access
4. **Multi-tenant** support for different organizations

## 📊 Key Observations & Benefits

### 1. **Mythology Theme Effectiveness**
Using Greek mythology for dashboard naming creates memorable, intuitive associations:
- **Hermes** (messenger) = Sales communication and performance
- **Asclepius** (healing) = Client health and recovery
- **Athena** (wisdom) = Strategic project intelligence

### 2. **Voice Integration Value**
Voice commands provide hands-free operation, particularly valuable for:
- Sales reps during calls or driving
- Executives reviewing metrics during meetings
- Quick status checks without context switching

### 3. **Real-time Architecture Benefits**
WebSocket implementation enables:
- Immediate visibility into critical changes
- Collaborative awareness across team members
- Reduced cognitive load from constant manual refreshing

This implementation provides a solid foundation for AI-powered business intelligence with room for continuous enhancement based on user feedback and evolving business needs.