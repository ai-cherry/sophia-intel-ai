#!/usr/bin/env python3
import os
import re
import json
from collections import defaultdict, Counter

SRC_ROOT = os.path.join('agent-ui', 'src')

PATTERNS = {
    'api_calls': re.compile(r"\\b(fetch|axios)\\b"),
    'state_hooks': re.compile(r"\\b(useState|useReducer|useContext|zustand|redux)\\b"),
    'charts': re.compile(r"recharts|\\bd3\\b|chart\\.js|plotly|visx"),
}

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ''

def collect_files(root):
    ts_like = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(('.ts', '.tsx')):
                ts_like.append(os.path.join(dirpath, fn))
    return ts_like

def analyze_file(path):
    text = read_file(path)
    realtime_counts = Counter()
    for token in ["WebSocket", "EventSource", "SSE", "socket.io"]:
        realtime_counts[token] += len(re.findall(re.escape(token), text))
    # Handle plain 'io(' separately to avoid regex pitfalls
    realtime_counts['io('] += text.count('io(')

    # API counts (simplified)
    api_counts = Counter()
    api_counts['fetch'] += len(re.findall(r"fetch\s*\(", text))
    api_counts['axios'] += len(re.findall(r"axios\s*\(", text))

    # State hooks counts (robust to spacing)
    state_counts = Counter()
    for token in ["useState", "useReducer", "useContext", "zustand", "redux"]:
        state_counts[token] += text.count(token)

    result = {
        'api_calls': api_counts,
        'state_hooks': state_counts,
        'realtime': realtime_counts,
        'charts': Counter(PATTERNS['charts'].findall(text)),
    }
    return result

def main():
    files = collect_files(SRC_ROOT)
    dashboards = []
    chat_components = []
    hooks = []

    per_file = {}
    totals = {
        'api_calls': Counter(),
        'state_hooks': Counter(),
        'realtime': Counter(),
        'charts': Counter(),
    }

    for f in files:
        af = analyze_file(f)
        per_file[f] = af
        for k in totals:
            totals[k].update(af[k])

        # classify
        lower = f.lower()
        base = os.path.basename(f)
        if ('dashboard' in lower) or ('components/dashboards/' in f.replace('\\\\','/')):
            dashboards.append(f)
        if ('/playground/chatarea/' in f.replace('\\\\','/').lower()) or re.search(r"(Chat|Message)", base):
            chat_components.append(f)
        if '/hooks/' in f.replace('\\\\','/'):
            hooks.append(f)

    summary = {
        'scanned_files': len(files),
        'dashboards_count': len(sorted(set(dashboards))),
        'chat_components_count': len(sorted(set(chat_components))),
        'api_calls_totals': dict(totals['api_calls']),
        'state_hooks_totals': dict(totals['state_hooks']),
        'realtime_totals': dict(totals['realtime']),
        'charts_totals': dict(totals['charts']),
    }

    # Top files by category
    def top_files(category_key, top_n=10):
        counts = []
        for f, data in per_file.items():
            counts.append((f, sum(data[category_key].values())))
        counts.sort(key=lambda x: x[1], reverse=True)
        return [ {'file': f, 'count': c} for f, c in counts if c>0][:top_n]

    analysis = {
        'summary': summary,
        'lists': {
            'dashboards': sorted(set(dashboards)),
            'chat_components': sorted(set(chat_components)),
            'hooks': sorted(set(hooks)),
        },
        'top_files': {
            'api_calls': top_files('api_calls'),
            'state_hooks': top_files('state_hooks'),
            'realtime': top_files('realtime'),
            'charts': top_files('charts'),
        },
        'per_file': per_file,
    }

    os.makedirs('sophia_analysis', exist_ok=True)

    # Write JSON
    with open('sophia_analysis/complete_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2)

    # Write UNIFICATION_REPORT.md
    with open('sophia_analysis/UNIFICATION_REPORT.md', 'w', encoding='utf-8') as f:
        s = analysis['summary']
        f.write('# SOPHIA UI Unification Report\n\n')
        f.write('## Summary\n')
        f.write(f"- Files scanned: {s['scanned_files']}\n")
        f.write(f"- Dashboards: {s['dashboards_count']}\n")
        f.write(f"- Chat components: {s['chat_components_count']}\n")
        f.write(f"- API calls: {s['api_calls_totals']}\n")
        f.write(f"- State hooks: {s['state_hooks_totals']}\n")
        f.write(f"- Realtime: {s['realtime_totals']}\n")
        f.write(f"- Charts: {s['charts_totals']}\n\n")

        f.write('## Dashboards\n')
        for path in analysis['lists']['dashboards']:
            f.write(f"- `{path}`\n")
        f.write('\n## Chat Components\n')
        for path in analysis['lists']['chat_components']:
            f.write(f"- `{path}`\n")
        f.write('\n## Top Files\n')
        for cat in ['api_calls','state_hooks','realtime','charts']:
            f.write(f"\n### {cat}\n")
            for item in analysis['top_files'][cat]:
                f.write(f"- `{item['file']}` — {item['count']}\n")

    # Write SOPHIA_UNIFIED_DESIGN_PLAN.md
    with open('sophia_analysis/SOPHIA_UNIFIED_DESIGN_PLAN.md', 'w', encoding='utf-8') as f:
        f.write('# SOPHIA Unified Design Plan\n\n')
        f.write('## Architecture Overview\n')
        f.write('- State management: Zustand (already in use via `agent-ui/src/store.ts`).\n')
        f.write('- Real-time: Primary WebSocket with SSE fallback; centralize in a `RealtimeManager`.\n')
        f.write('- API layer: typed fetch wrappers; consolidate endpoints in `agent-ui/src/api`.\n')
        f.write('- Module structure: Dashboards, Chat, Streams, MCP, Model Registry, Analytics, Playground.\n')
        f.write('- Shared widget library: charts, cards, status, stream display.\n\n')

        f.write('## Key Modules To Create/Consolidate\n')
        f.write('- `lib/realtime/RealtimeManager.ts`: single connection manager with auto-retry and SSE fallback.\n')
        f.write('- `lib/api/client.ts`: fetch/axios wrapper with interceptors and error normalization.\n')
        f.write('- `lib/state/unifiedStore.ts`: thin layer reusing Zustand slices for dashboards/chat.\n')
        f.write('- `components/widgets/*`: extract shared cards, tables, charts from dashboards.\n')
        f.write('- `components/chat/*`: unify ChatArea and hooks around `useAIStreamHandler`.\n\n')

        f.write('## Roadmap (11 Weeks)\n')
        f.write('- Weeks 1–2: Core infrastructure (RealtimeManager, API client, store slices).\n')
        f.write('- Weeks 3–4: Extract shared widgets from dashboards; standardize props.\n')
        f.write('- Weeks 5–6: CommandCenter: compose dashboards into unified routes/layout.\n')
        f.write('- Week 7: Chat consolidation across Playground and Stream displays.\n')
        f.write('- Week 8: Agent orchestration UI harmonization (swarm, MCP status, prompts).\n')
        f.write('- Week 9: Intelligence hub integrations (analytics, cost/model registry).\n')
        f.write('- Week 10: Testing and performance; storybook for widgets.\n')
        f.write('- Week 11: Deployment playbook; feature flags and rollout.\n\n')

        f.write('## Cross-References\n')
        f.write('- Dashboards to widgets: see UNIFICATION_REPORT for extraction targets.\n')
        f.write('- Chat to streams: consolidate around `hooks/useAIStreamHandler.tsx`.\n')
        f.write('- Realtime hotspots: top files under `top_files.realtime`.\n')
        f.write('- API hotspots: top files under `top_files.api_calls`.\n')

    # Write IMPLEMENTATION_ROADMAP.md with cross-references
    def file_api_count(p):
        d = per_file.get(p, {})
        return int(sum(d.get('api_calls', {}).values()))
    def file_rt_count(p):
        d = per_file.get(p, {})
        return int(sum(d.get('realtime', {}).values()))

    dashboards_info = [
        {
            'path': p,
            'api_calls': file_api_count(p),
            'realtime': file_rt_count(p),
        }
        for p in analysis['lists']['dashboards']
    ]
    chat_info = [
        {
            'path': p,
            'api_calls': file_api_count(p),
            'realtime': file_rt_count(p),
        }
        for p in analysis['lists']['chat_components']
    ]

    with open('sophia_analysis/IMPLEMENTATION_ROADMAP.md', 'w', encoding='utf-8') as f:
        f.write('# Implementation Roadmap (Cross-Referenced)\n\n')
        f.write('## Overview\n')
        f.write(f"- Dashboards: {summary['dashboards_count']}\n")
        f.write(f"- Chat components: {summary['chat_components_count']}\n")
        f.write(f"- Realtime totals: {summary['realtime_totals']}\n")
        f.write(f"- API totals: {summary['api_calls_totals']}\n\n")

        f.write('## Dashboards: API & Realtime Heatmap\n')
        for item in sorted(dashboards_info, key=lambda x: (x['realtime'], x['api_calls']), reverse=True):
            f.write(f"- `{item['path']}` — RT: {item['realtime']}, API: {item['api_calls']}\n")

        f.write('\n## Chat Components: API & Realtime Heatmap\n')
        for item in sorted(chat_info, key=lambda x: (x['realtime'], x['api_calls']), reverse=True):
            f.write(f"- `{item['path']}` — RT: {item['realtime']}, API: {item['api_calls']}\n")

        f.write('\n## Week-by-Week Actions\n')
        f.write('- Weeks 1–2: Implement `lib/realtime/RealtimeManager.ts` and `lib/api/client.ts`; wire into top 5 realtime/API hotspots.\n')
        f.write('- Weeks 3–4: Extract shared widgets from highest-RT dashboards first (see heatmap).\n')
        f.write('- Weeks 5–6: Build `CommandCenter` layout and route aggregation; replace per-dashboard state with store slices.\n')
        f.write('- Week 7: Unify ChatArea + stream display using `useAIStreamHandler` and RealtimeManager.\n')
        f.write('- Week 8: Harmonize MCP/Swarm UIs and endpoint selectors.\n')
        f.write('- Week 9: Integrate analytics and model registry views with unified widgets.\n')
        f.write('- Week 10: Add tests and Storybook stories for widgets and managers.\n')
        f.write('- Week 11: Toggle-based rollout; monitor RT/API error rates.\n')

if __name__ == '__main__':
    main()
