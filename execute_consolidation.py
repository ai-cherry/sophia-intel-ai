#!/usr/bin/env python3
"""
Sophia Intel AI - Consolidation Execution Script
This script implements the three-part consolidation plan
"""

import os
import json
import glob
from pathlib import Path
from typing import List, Dict, Any

class SophiaConsolidator:
    def __init__(self):
        self.project_root = Path.cwd()
        self.report = []
        
    def find_all_dashboards(self) -> List[Path]:
        """Find all dashboard files in the project"""
        patterns = ['*dashboard*', '*bi*', '*sophia*']
        extensions = ['.html', '.jsx', '.tsx', '.svelte', '.vue', '.py']
        
        dashboards = []
        for pattern in patterns:
            for ext in extensions:
                dashboards.extend(self.project_root.rglob(f'{pattern}{ext}'))
        
        # Filter out node_modules and .git
        dashboards = [d for d in dashboards if 'node_modules' not in str(d) and '.git' not in str(d)]
        return dashboards
    
    def analyze_dashboard(self, path: Path) -> Dict[str, Any]:
        """Analyze a dashboard file for features"""
        with open(path, 'r') as f:
            content = f.read()
            
        return {
            'path': str(path.relative_to(self.project_root)),
            'size': len(content),
            'has_integrations': any(x in content.lower() for x in ['slack', 'gong', 'hubspot', 'salesforce']),
            'has_websocket': 'websocket' in content.lower(),
            'has_chat': 'chat' in content.lower(),
            'framework': self.detect_framework(content)
        }
    
    def detect_framework(self, content: str) -> str:
        """Detect the framework used"""
        if 'svelte' in content.lower():
            return 'Svelte'
        elif 'react' in content.lower() or 'jsx' in content:
            return 'React'
        elif 'vue' in content.lower():
            return 'Vue'
        else:
            return 'Vanilla'
    
    def run_consolidation(self):
        """Execute the consolidation plan"""
        print('🔍 PHASE 1: Discovery')
        print('=' * 50)
        
        dashboards = self.find_all_dashboards()
        print(f'Found {len(dashboards)} dashboard-related files')
        
        for dash in dashboards[:10]:  # Show first 10
            analysis = self.analyze_dashboard(dash)
            print(f'  - {analysis["path"]}')
            print(f'    Framework: {analysis["framework"]}, Size: {analysis["size"]} bytes')
            print(f'    Integrations: {analysis["has_integrations"]}, Chat: {analysis["has_chat"]}')
        
        print()
        print('📊 Recommendation:')
        print('  Primary dashboard should be: ./dashboard/sophia_bi.html')
        print('  Consolidate features from all others')
        print('  Delete duplicates after merging')
        
if __name__ == '__main__':
    consolidator = SophiaConsolidator()
    consolidator.run_consolidation()
