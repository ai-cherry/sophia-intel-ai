#!/bin/bash

echo "🔍 SOPHIA UNIFIED ANALYSIS - PARALLEL EXECUTION"
echo "==============================================="

# Create output directory
mkdir -p sophia_analysis

# Run all analyses in parallel using background processes
echo "🚀 Launching parallel analysis..."

# 1. Find all dashboard/chat/message component files by filename
find agent-ui/src -type f \( -iname "*Dashboard*.tsx" -o -iname "*Chat*.tsx" -o -iname "*Message*.tsx" \) > sophia_analysis/all_components.txt &

# 2. Extract all imports and exports
grep -rE '^(import|export)' agent-ui/src --include="*.tsx" --include="*.ts" > sophia_analysis/imports.txt 2>/dev/null &

# 3. Find all API calls
grep -rE 'fetch|axios|api|endpoint' agent-ui/src --include="*.tsx" --include="*.ts" > sophia_analysis/api_calls.txt 2>/dev/null &

# 4. Extract all state management
grep -rE 'useState|useReducer|zustand|redux|useContext' agent-ui/src --include="*.tsx" > sophia_analysis/state_patterns.txt 2>/dev/null &

# 5. Find all real-time patterns
grep -rE 'WebSocket|EventSource|SSE|socket\.io|io\(' agent-ui/src --include="*.tsx" --include="*.ts" > sophia_analysis/realtime.txt 2>/dev/null &

# 6. Extract chart libraries
grep -rE 'recharts|d3|chart\.js|plotly|visx' agent-ui/src --include="*.tsx" > sophia_analysis/charts.txt 2>/dev/null &

# 7. Find all hooks
grep -rE '^(export.*use[A-Z]|const.*use[A-Z])' agent-ui/src --include="*.tsx" --include="*.ts" > sophia_analysis/hooks.txt 2>/dev/null &

# 8. Extract all types and interfaces
grep -rE '^(interface|type|export interface|export type)\b' agent-ui/src --include="*.tsx" --include="*.ts" > sophia_analysis/types.txt 2>/dev/null &

# Wait for all background processes
wait

echo "✅ Analysis complete! Generating unified report..."

# Generate unified analysis report with dynamic counts
cat > sophia_analysis/unified_report.md <<REPORT
# SOPHIA UNIFIED ANALYSIS REPORT

## Components Found
$(wc -l < sophia_analysis/all_components.txt) total components (by filename match)

## Dashboards Identified (by content)
$(find agent-ui/src -type f -name "*.tsx" -print0 2>/dev/null | xargs -0 grep -l -E "Dashboard" 2>/dev/null | wc -l) dashboard components

## Chat Components (by content)
$(find agent-ui/src -type f -name "*.tsx" -print0 2>/dev/null | xargs -0 grep -l -E "Chat|Message" 2>/dev/null | wc -l) chat components

## API Patterns
$(grep -oE "fetch|axios" sophia_analysis/api_calls.txt | sort | uniq -c)

## State Management
$(grep -oE "useState|useReducer|zustand|redux|useContext" sophia_analysis/state_patterns.txt | sort | uniq -c)

## Real-time Communication
$(grep -oE "WebSocket|EventSource|SSE|socket\.io|io\(" sophia_analysis/realtime.txt | sort | uniq -c)

## Visualization Libraries
$(grep -oE "recharts|d3|plotly|chart\.js|visx" sophia_analysis/charts.txt | sort | uniq -c)
REPORT

echo "📊 Analysis saved to sophia_analysis/"

# Extended analysis: generate JSON + design/roadmap docs
if command -v python3 >/dev/null 2>&1; then
  echo "🧠 Generating deep analysis and design artifacts..."
  python3 tools/ui_unification_analysis.py || echo "(warn) Extended analysis failed"
  echo "📁 Created: complete_analysis.json, UNIFICATION_REPORT.md, SOPHIA_UNIFIED_DESIGN_PLAN.md, IMPLEMENTATION_ROADMAP.md"
else
  echo "(warn) python3 not found; skipping deep analysis"
fi
