#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
from datetime import datetime

class DashboardConsolidator:
    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / f'dashboard_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        self.report = []
        
    def run(self):
        print('Starting Dashboard Consolidation')
        print('=' * 50)
        
        # Create backup
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup existing dashboards
        dashboards = [
            'sophia_business_intelligence.html',
            'sophia_main.html'
        ]
        
        for dashboard in dashboards:
            src = self.project_root / dashboard
            if src.exists():
                dst = self.backup_dir / dashboard
                shutil.copy2(src, dst)
                print(f'Backed up: {dashboard}')
        
        print('Consolidation started - see CONSOLIDATION_REPORT.md')

if __name__ == '__main__':
    DashboardConsolidator().run()
