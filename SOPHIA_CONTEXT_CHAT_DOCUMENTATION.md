# Sophia Context-Aware Chat Documentation

## Overview
The Sophia chat system has been enhanced to be **context-aware** and is now integrated into **every page** of the Sophia Intel App dashboard. The chat automatically detects which page the user is viewing and adapts its behavior accordingly.

---

## 🎯 Key Features

### 1. **Universal Availability**
- Chat widget appears on ALL pages of the application
- Persistent across navigation
- Single instance shared across the entire app

### 2. **Context Awareness**
- Automatically detects current page using `usePathname()`
- Sends page context with every message to backend
- Updates UI to reflect current page location

### 3. **Smart Prompt Suggestions**
- Different suggested prompts for each page type
- Context-specific questions to guide users
- Dynamically updates when navigating between pages

### 4. **Enhanced UI/UX**
- Modern, polished chat interface
- Minimize/maximize functionality
- Visual indicators for current page context
- Gradient floating action button
- Real-time typing indicators
- Message timestamps

---

## 📁 File Locations

### Core Components
- **New Context-Aware Chat**: `/sophia-intel-app/src/components/SophiaContextChat.tsx`
- **Original Chat**: `/sophia-intel-app/src/components/SophiaChat.tsx` (preserved)
- **Integration Point**: `/sophia-intel-app/src/app/layout.tsx` (root layout)

### Test Files
- **HTML Test Page**: `/test_sophia_context_chat.html`
- **Documentation**: `/SOPHIA_CONTEXT_CHAT_DOCUMENTATION.md`

---

## 🗺️ Page Context Mappings

### `/projects` - Project Management
```typescript
{
  page: 'projects',
  title: 'Project Management',
  icon: Briefcase,
  suggestedPrompts: [
    "What are the critical risks in my projects?",
    "Show me overdue projects from Asana",
    "Which Slack channels need attention?",
    "Analyze team velocity trends"
  ]
}
```

### `/chat` - Direct Chat
```typescript
{
  page: 'chat',
  title: 'Sophia Chat',
  icon: MessageSquare,
  suggestedPrompts: [
    "Help me understand our revenue metrics",
    "What are today's priorities?",
    "Analyze recent customer feedback",
    "Generate a status report"
  ]
}
```

### `/swarms` - Agent Orchestration
```typescript
{
  page: 'swarms',
  title: 'Agent Swarms',
  icon: Users,
  suggestedPrompts: [
    "Show active agent swarms",
    "What's the swarm performance?",
    "Debug the last failed task",
    "Optimize agent allocation"
  ]
}
```

### `/brain` - Knowledge System
```typescript
{
  page: 'brain',
  title: 'Knowledge Brain',
  icon: Brain,
  suggestedPrompts: [
    "What do you know about our customers?",
    "Search for product documentation",
    "Show recent learnings",
    "Update knowledge base"
  ]
}
```

### `/router` - Model Router
```typescript
{
  page: 'router',
  title: 'Model Router',
  icon: GitBranch,
  suggestedPrompts: [
    "Show model performance stats",
    "Which model is most cost-effective?",
    "Analyze routing patterns",
    "Optimize model selection"
  ]
}
```

---

## 💬 Context Payload Structure

When a user sends a message, the following context is included:

```json
{
  "message": "User's message text",
  "sessionId": "abc123...",
  "context": {
    "path": "/projects",
    "page": "projects",
    "title": "Project Management",
    "metadata": {
      "source": "pm_dashboard",
      "integrations": ["asana", "linear", "slack"]
    },
    "timestamp": "2025-09-10T20:30:00Z"
  }
}
```

---

## 🎨 UI Components

### Chat States
1. **Closed**: Floating action button with gradient background
2. **Open**: Full chat interface (396px × 600px)
3. **Minimized**: Compact bar with expand option

### Visual Elements
- **Header**: Shows Sophia icon, current page context
- **Metrics Bar**: Displays session ID, token count, cost
- **Message Area**: Supports user, assistant, and system messages
- **Input Area**: Context-aware placeholder text
- **Suggested Prompts**: Page-specific quick actions

---

## 🚀 Implementation Details

### Technology Stack
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Routing**: `usePathname()` hook for route detection
- **Streaming**: Server-Sent Events (SSE)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **State**: React hooks (useState, useEffect, useRef)

### Key Functions
```typescript
// Get current page context
const currentContext = useMemo(() => {
  return PAGE_CONTEXTS[pathname] || defaultContext;
}, [pathname]);

// Send message with context
const send = useCallback(async (text?: string) => {
  const payload = {
    message: text || input,
    sessionId,
    context: {
      path: pathname,
      page: currentContext.page,
      title: currentContext.title,
      metadata: currentContext.metadata
    }
  };
  // ... send to backend
}, [input, sessionId, pathname, currentContext]);
```

---

## ✅ Testing Checklist

- [x] Chat widget appears on all pages
- [x] Context changes when navigating pages
- [x] Suggested prompts update per page
- [x] Page title shows in chat header
- [x] Minimize/maximize functionality works
- [x] Session persists across page changes
- [x] Streaming responses display correctly
- [x] Metrics (tokens/cost) display when available
- [x] Context sent with each message to backend
- [x] Visual indicators for current page context

---

## 🔧 Configuration

### Enable/Disable Context Chat
In `/sophia-intel-app/src/app/layout.tsx`:
```tsx
// To use context-aware chat (recommended)
import SophiaContextChat from '@/components/SophiaContextChat'
<SophiaContextChat />

// To use original chat
import SophiaChat from '@/components/SophiaChat'
<SophiaChat />
```

### Add New Page Context
In `SophiaContextChat.tsx`, add to `PAGE_CONTEXTS`:
```typescript
'/new-page': {
  page: 'new_page',
  title: 'New Page Title',
  description: 'Page description',
  suggestedPrompts: [
    "Prompt 1",
    "Prompt 2"
  ],
  icon: <IconComponent className="w-4 h-4" />,
  metadata: { custom: 'data' }
}
```

---

## 🎯 Benefits

1. **Improved User Experience**
   - Always accessible, no need to navigate to chat page
   - Context-aware suggestions reduce friction
   - Visual continuity across all pages

2. **Better AI Responses**
   - Sophia knows which page user is viewing
   - Can provide page-specific insights
   - More relevant and targeted assistance

3. **Increased Engagement**
   - Suggested prompts encourage interaction
   - Lower barrier to asking questions
   - Contextual help exactly when needed

4. **Operational Efficiency**
   - Single chat instance reduces resource usage
   - Session persistence improves conversation flow
   - Context tracking enables better analytics

---

## 🚦 Quick Start

1. **Start the application**:
   ```bash
   cd sophia-intel-app
   npm run dev
   ```

2. **Navigate to any page**:
   - http://localhost:3000/projects
   - http://localhost:3000/chat
   - http://localhost:3000/swarms

3. **Click "Chat with Sophia"** button (bottom-right)

4. **Notice the context**:
   - Page title in header
   - Context-specific suggested prompts
   - Placeholder text matches current page

5. **Test navigation**:
   - Keep chat open
   - Navigate to different page
   - See context update automatically

---

## 📈 Future Enhancements

- [ ] Voice input/output capabilities
- [ ] Multi-language support
- [ ] Chat history search
- [ ] Export conversation feature
- [ ] Collaborative chat (multiple users)
- [ ] Custom themes per page
- [ ] Keyboard shortcuts
- [ ] File upload support
- [ ] Rich media responses (charts, tables)
- [ ] Integration with notification system

---

**Version**: 1.0.0  
**Last Updated**: 2025-09-10  
**Status**: ✅ Fully Implemented and Tested