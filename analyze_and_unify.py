#!/usr/bin/env python3

import os
import re
import json
import ast
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set
import concurrent.futures

class SophiaAnalyzer:
    def __init__(self, base_path="agent-ui/src"):
        self.base_path = Path(base_path)
        self.components = defaultdict(list)
        self.imports = defaultdict(set)
        self.apis = defaultdict(list)
        self.state_patterns = defaultdict(int)
        self.realtime_patterns = defaultdict(int)
        
    def analyze_all(self):
        """Run all analyses in parallel"""
        tsx_files = list(self.base_path.rglob("*.tsx"))
        ts_files = list(self.base_path.rglob("*.ts"))
        all_files = tsx_files + ts_files
        
        print(f"🔍 Analyzing {len(all_files)} files...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for file_path in all_files:
                futures.append(executor.submit(self.analyze_file, file_path))
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error: {e}")
        
        return self.generate_report()
    
    def analyze_file(self, file_path):
        """Analyze a single file"""
        try:
            content = file_path.read_text()
            
            # Categorize component
            if "Dashboard" in file_path.name:
                self.components["dashboards"].append(str(file_path))
            elif "Chat" in file_path.name or "Message" in file_path.name:
                self.components["chat"].append(str(file_path))
            elif "Agent" in file_path.name:
                self.components["agents"].append(str(file_path))
            elif "Intel" in file_path.name or "Intelligence" in file_path.name:
                self.components["intelligence"].append(str(file_path))
            elif "Command" in file_path.name:
                self.components["command"].append(str(file_path))
            
            # Extract patterns
            self.extract_imports(content, file_path)
            self.extract_apis(content, file_path)
            self.extract_state(content, file_path)
            self.extract_realtime(content, file_path)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def extract_imports(self, content, file_path):
        """Extract all imports"""
        import_pattern = r"import\s+.*?from\s+['\"](.+?)['\"]"
        imports = re.findall(import_pattern, content)
        for imp in imports:
            self.imports[str(file_path)].add(imp)
    
    def extract_apis(self, content, file_path):
        """Extract API calls"""
        api_patterns = [
            r"fetch\(['\"](.+?)['\"]",
            r"axios\.(get|post|put|delete)\(['\"](.+?)['\"]",
            r"api\.(get|post|put|delete)\(['\"](.+?)['\"]"
        ]
        for pattern in api_patterns:
            matches = re.findall(pattern, content)
            if matches:
                self.apis[str(file_path)].extend(matches)
    
    def extract_state(self, content, file_path):
        """Extract state management patterns"""
        patterns = ["useState", "useReducer", "zustand", "redux", "useContext"]
        for pattern in patterns:
            count = len(re.findall(pattern, content))
            if count > 0:
                self.state_patterns[pattern] += count
    
    def extract_realtime(self, content, file_path):
        """Extract real-time patterns"""
        patterns = ["WebSocket", "EventSource", "SSE", "socket.io", "io("]
        for pattern in patterns:
            count = len(re.findall(pattern, content))
            if count > 0:
                self.realtime_patterns[pattern] += count
    
    def generate_report(self):
        """Generate comprehensive report"""
        report = {
            "summary": {
                "total_files": len(self.imports),
                "dashboards": len(self.components["dashboards"]),
                "chat_components": len(self.components["chat"]),
                "agent_components": len(self.components["agents"]),
                "intelligence_components": len(self.components["intelligence"]),
                "command_components": len(self.components["command"]),
                "unique_imports": len(set().union(*self.imports.values())) if self.imports else 0,
                "api_endpoints": sum(len(v) for v in self.apis.values()),
            },
            "components": dict(self.components),
            "state_patterns": dict(self.state_patterns),
            "realtime_patterns": dict(self.realtime_patterns),
            "top_imports": self.get_top_imports(),
            "unification_plan": self.generate_unification_plan()
        }
        
        # Create output directory
        Path("sophia_analysis").mkdir(exist_ok=True)
        
        # Save report
        with open("sophia_analysis/complete_analysis.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown report
        self.generate_markdown_report(report)
        
        return report
    
    def get_top_imports(self, limit=20):
        """Get most common imports"""
        import_counts = defaultdict(int)
        for imports in self.imports.values():
            for imp in imports:
                import_counts[imp] += 1
        return dict(sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:limit])
    
    def generate_unification_plan(self):
        """Generate unification strategy"""
        return {
            "architecture": "micro-frontend",
            "state_management": "zustand" if self.state_patterns.get("zustand", 0) > 0 else "context",
            "realtime": "WebSocket" if self.realtime_patterns.get("WebSocket", 0) > 0 else "SSE",
            "modules_to_create": [
                "core/UnifiedStore",
                "core/UnifiedAPI",
                "core/RealtimeManager",
                "modules/CommandCenter",
                "modules/IntelligenceHub",
                "modules/UnifiedChat",
                "modules/AgentOrchestrator"
            ],
            "migration_phases": [
                "Extract shared components",
                "Unify API layer",
                "Consolidate state management",
                "Merge dashboards",
                "Integrate chat system",
                "Add agent orchestration",
                "Implement intelligence hub"
            ]
        }
    
    def generate_markdown_report(self, report):
        """Generate detailed markdown report"""
        md = f"""# SOPHIA UNIFIED SYSTEM ANALYSIS

## 📊 Summary
- **Total Files Analyzed**: {report['summary']['total_files']}
- **Dashboard Components**: {report['summary']['dashboards']}
- **Chat Components**: {report['summary']['chat_components']}
- **Agent Components**: {report['summary']['agent_components']}
- **Intelligence Components**: {report['summary']['intelligence_components']}
- **Command Components**: {report['summary']['command_components']}
- **Unique Imports**: {report['summary']['unique_imports']}
- **API Endpoints**: {report['summary']['api_endpoints']}

## 🏗️ Architecture Recommendation
Based on analysis, recommended architecture: **{report['unification_plan']['architecture']}**

## 📁 Components to Unify

### Dashboards Found:
"""
        for dashboard in report['components'].get('dashboards', [])[:10]:
            md += f"- {Path(dashboard).name}\n"
        
        md += "\n### Chat Components Found:\n"
        for chat in report['components'].get('chat', [])[:10]:
            md += f"- {Path(chat).name}\n"
        
        md += "\n### Agent Components Found:\n"
        for agent in report['components'].get('agents', [])[:10]:
            md += f"- {Path(agent).name}\n"
        
        md += f"""
## 🔧 Technical Stack

### State Management
"""
        for pattern, count in report['state_patterns'].items():
            md += f"- {pattern}: {count} uses\n"
        
        md += "\n### Real-time Communication\n"
        for pattern, count in report['realtime_patterns'].items():
            md += f"- {pattern}: {count} uses\n"
        
        md += f"""

## 🎯 Top Imports (Most Used Dependencies)
"""
        for imp, count in list(report['top_imports'].items())[:15]:
            md += f"- {imp}: {count} files\n"
        
        md += f"""

## 🚀 Unification Plan

### Phase 1: Core Infrastructure
```typescript
// Create unified data layer
export class UnifiedDataLayer {{
  private api: UnifiedAPI;
  private store: UnifiedStore;
  private realtime: RealtimeManager;
  
  async initialize() {{
    // Connect all systems
  }}
}}
```

### Phase 2: Module Integration
"""
        for module in report['unification_plan']['modules_to_create']:
            md += f"- Create `{module}`\n"
        
        md += f"""

### Phase 3: Migration Steps
"""
        for i, phase in enumerate(report['unification_plan']['migration_phases'], 1):
            md += f"{i}. {phase}\n"
        
        md += f"""

## 🔄 Recommended State Management
**{report['unification_plan']['state_management']}**

## 📡 Recommended Real-time Protocol
**{report['unification_plan']['realtime']}**

## 📝 Next Steps
1. Review component dependencies
2. Create shared component library
3. Implement unified API client
4. Build centralized state store
5. Integrate all dashboards into single command center
6. Deploy unified SOPHIA system
"""
        
        # Save markdown report
        with open("sophia_analysis/UNIFICATION_REPORT.md", "w") as f:
            f.write(md)
        
        print(f"✅ Report saved to sophia_analysis/UNIFICATION_REPORT.md")

# Run the analyzer
if __name__ == "__main__":
    analyzer = SophiaAnalyzer()
    report = analyzer.analyze_all()
    
    print("\n" + "="*60)
    print("📊 ANALYSIS COMPLETE")
    print("="*60)
    print(f"Total files analyzed: {report['summary']['total_files']}")
    print(f"Dashboards found: {report['summary']['dashboards']}")
    print(f"Chat components: {report['summary']['chat_components']}")
    print(f"Agent components: {report['summary']['agent_components']}")
    print(f"Intelligence components: {report['summary']['intelligence_components']}")
    print(f"Command components: {report['summary']['command_components']}")
    print(f"\n✅ Full report saved to sophia_analysis/")