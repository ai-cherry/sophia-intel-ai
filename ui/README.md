# Agno Agent UI

A local-first UI for interacting with AI agent swarms and workflows via the Agno Playground.

## Features

- 🔒 **Local-first**: No secrets stored in browser, all LLM calls through backend
- 🚀 **Real-time streaming**: See tokens as they arrive
- 🎯 **Team & Workflow support**: Run coding swarms and complex workflows
- 📊 **Quality visibility**: Critic reviews, Judge decisions, Runner gates
- 🔍 **Tool inspection**: View all tool calls with expandable details
- 📝 **Code citations**: See referenced code with `path:line` format
- ♿ **Accessible**: WCAG compliant with keyboard navigation
- 🛡️ **Secure**: CSP headers, XSS protection, secure defaults

## Prerequisites

- Node.js 20+
- pnpm (or npm/yarn)
- Agno Playground running on `http://localhost:7777`

## Installation

```bash
# Install dependencies
pnpm install

# Copy environment variables
cp .env.local.example .env.local
# (Edit .env.local if needed)
```

## Development

```bash
# Start dev server
pnpm dev

# Open http://localhost:3000
```

## Usage

1. **Connect to Playground**
   - Enter endpoint URL (default: `http://localhost:7777`)
   - Click "Connect" and verify green status

2. **Run Teams**
   - Go to Chat page
   - Select a team (e.g., Coding Swarm)
   - Enter your task/question
   - Optionally set pool (fast/balanced/heavy) and priority
   - Click "Run Team"

3. **Run Workflows**
   - Go to Workflow page
   - Select workflow (e.g., PR Lifecycle)
   - Enter task and additional data (JSON)
   - Click "Run Workflow"
   - View quality gates and Judge decisions

## Testing

```bash
# Type checking
pnpm typecheck

# Linting
pnpm lint

# E2E tests (Playwright)
pnpm test:e2e

# E2E with UI
pnpm test:e2e:ui
```

## Building

```bash
# Production build
pnpm build

# Start production server
pnpm start
```

## Project Structure

```
ui/
├── src/
│   ├── lib/          # Core utilities
│   │   ├── endpoint.ts    # Endpoint management
│   │   ├── fetch.ts       # HTTP with retry
│   │   ├── sse.ts         # Server-sent events
│   │   └── types.ts       # TypeScript types
│   ├── state/        # State management
│   │   └── ui.ts          # Zustand store
│   ├── components/   # React components
│   │   ├── EndpointPicker.tsx
│   │   ├── TeamWorkflowPanel.tsx
│   │   ├── StreamView.tsx
│   │   ├── JudgeReport.tsx
│   │   ├── CriticReport.tsx
│   │   ├── ToolCalls.tsx
│   │   └── Citations.tsx
│   └── pages/        # Next.js pages
│       ├── index.tsx      # Home
│       ├── chat.tsx       # Team runner
│       └── workflow.tsx   # Workflow runner
├── tests/
│   └── e2e/          # Playwright tests
└── public/           # Static assets
```

## Security

- **No secrets in browser**: All API keys stay on backend
- **CSP headers**: Strict Content Security Policy
- **XSS protection**: React's built-in escaping
- **CORS**: Backend must allow `http://localhost:3000`

## Environment Variables

```bash
# Playground endpoint (no trailing slash)
NEXT_PUBLIC_DEFAULT_ENDPOINT=http://localhost:7777

# App name shown in UI
NEXT_PUBLIC_APP_NAME=slim-agno

# Stream timeout in milliseconds
NEXT_PUBLIC_STREAM_TIMEOUT_MS=600000
```

## Troubleshooting

### Connection fails
- Verify Playground is running: `curl http://localhost:7777/healthz`
- Check CORS settings on backend
- Try different browser (some extensions block local connections)

### No teams/workflows showing
- Ensure `/agents` and `/workflows` endpoints exist
- Check browser console for errors
- Verify endpoint URL has no trailing slash

### Streaming not working
- Check if backend supports SSE (Server-Sent Events)
- Verify `/run/team` and `/run/workflow` endpoints
- Look for timeout errors (increase `NEXT_PUBLIC_STREAM_TIMEOUT_MS`)

## CI/CD

GitHub Actions workflow included:
- Type checking
- Linting
- Building
- Playwright E2E tests
- Lighthouse performance audit
- Artifact uploads

## Future Enhancements

- [ ] History page with SQLite persistence
- [ ] WebSocket support for bi-directional streaming
- [ ] Dark mode
- [ ] Export/import task configurations
- [ ] Batch execution mode
- [ ] Real-time collaboration features

## License

MIT