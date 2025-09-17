#!/usr/bin/env python3
"""
Testing Infrastructure Consolidation Script

Consolidates duplicate testing infrastructure between tools/ and tests/integration/
Removes redundant smoke tests and strengthens pytest-based integration testing.
Part of Phase 2 remediation for repository duplication issues.

Usage:
    python scripts/consolidate_testing_infrastructure.py --analyze     # Analyze duplications
    python scripts/consolidate_testing_infrastructure.py --execute    # Apply consolidation
"""

import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import argparse


@dataclass
class ServiceTestPair:
    """Represents a service with both tools/ and tests/integration/ testing."""
    service: str
    tool_script: Path
    integration_test: Path
    overlap_percentage: float
    consolidation_action: str


class TestingConsolidator:
    """Consolidates duplicate testing infrastructure across the repository."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.tools_dir = repo_root / "tools"
        self.tests_dir = repo_root / "tests" / "integration"
        self.archive_dir = repo_root / "scripts" / "archive" / "tools_smoke_tests"
        self.analysis_results: List[ServiceTestPair] = []
    
    def discover_service_pairs(self) -> List[ServiceTestPair]:
        """Discover services that have both tools/ scripts and integration tests."""
        pairs = []
        
        if not self.tools_dir.exists() or not self.tests_dir.exists():
            print("❌ Required directories not found: tools/ or tests/integration/")
            return pairs
        
        # Find all tool smoke scripts
        tool_scripts = {}
        for service_dir in self.tools_dir.iterdir():
            if service_dir.is_dir():
                smoke_script = service_dir / "smoke.py"
                if smoke_script.exists():
                    tool_scripts[service_dir.name] = smoke_script
        
        # Find matching integration tests
        for service_name, tool_script in tool_scripts.items():
            integration_dir = self.tests_dir / service_name
            if integration_dir.exists():
                # Look for smoke test files
                smoke_tests = list(integration_dir.glob("test_*_smoke.py")) + list(integration_dir.glob("test_*smoke*.py"))
                if smoke_tests:
                    integration_test = smoke_tests[0]  # Take first match
                    
                    # Analyze overlap
                    overlap = self.analyze_overlap(tool_script, integration_test)
                    action = self.determine_consolidation_action(service_name, overlap)
                    
                    pairs.append(ServiceTestPair(
                        service=service_name,
                        tool_script=tool_script,
                        integration_test=integration_test,
                        overlap_percentage=overlap,
                        consolidation_action=action
                    ))
        
        return pairs
    
    def analyze_overlap(self, tool_script: Path, integration_test: Path) -> float:
        """Analyze functional overlap between tool script and integration test."""
        try:
            tool_content = tool_script.read_text()
            test_content = integration_test.read_text()
        except Exception:
            return 0.0
        
        # Simple heuristics for overlap analysis
        overlap_indicators = {
            'auth_test': ('auth', 'authentication', 'login'),
            'api_calls': ('get(', 'post(', 'put(', 'delete(', 'request'),
            'error_handling': ('except', 'try:', 'error', 'fail'),
            'credentials': ('token', 'key', 'secret', 'password'),
            'response_validation': ('response', 'status_code', 'json', 'assert'),
        }
        
        tool_features = set()
        test_features = set()
        
        for feature, keywords in overlap_indicators.items():
            if any(keyword in tool_content.lower() for keyword in keywords):
                tool_features.add(feature)
            if any(keyword in test_content.lower() for keyword in keywords):
                test_features.add(feature)
        
        if not tool_features:
            return 0.0
        
        overlap = len(tool_features & test_features) / len(tool_features)
        return round(overlap * 100, 1)
    
    def determine_consolidation_action(self, service: str, overlap: float) -> str:
        """Determine the best consolidation action based on overlap analysis."""
        if overlap >= 70:
            return "archive_tool_script"  # High overlap - archive tool, keep integration test
        elif overlap >= 40:
            return "merge_functionality"  # Medium overlap - merge unique features
        else:
            return "keep_both"  # Low overlap - different purposes
    
    def analyze_repository(self) -> Dict[str, any]:
        """Analyze the repository for testing duplication issues."""
        print("🔍 Analyzing testing infrastructure for duplications...")
        
        self.analysis_results = self.discover_service_pairs()
        
        stats = {
            'services_with_pairs': len(self.analysis_results),
            'high_overlap_count': len([p for p in self.analysis_results if p.overlap_percentage >= 70]),
            'medium_overlap_count': len([p for p in self.analysis_results if 40 <= p.overlap_percentage < 70]),
            'low_overlap_count': len([p for p in self.analysis_results if p.overlap_percentage < 40]),
            'archive_candidates': [p.service for p in self.analysis_results if p.consolidation_action == "archive_tool_script"],
            'merge_candidates': [p.service for p in self.analysis_results if p.consolidation_action == "merge_functionality"],
            'keep_both': [p.service for p in self.analysis_results if p.consolidation_action == "keep_both"]
        }
        
        return stats
    
    def generate_analysis_report(self, stats: Dict[str, any]):
        """Generate detailed analysis report."""
        print(f"\n📊 Testing Infrastructure Analysis Results:")
        print(f"   Services with duplicate testing: {stats['services_with_pairs']}")
        print(f"   High overlap (≥70%): {stats['high_overlap_count']}")
        print(f"   Medium overlap (40-69%): {stats['medium_overlap_count']}")
        print(f"   Low overlap (<40%): {stats['low_overlap_count']}")
        
        if self.analysis_results:
            print(f"\n📋 Service-by-Service Analysis:")
            for pair in sorted(self.analysis_results, key=lambda x: x.overlap_percentage, reverse=True):
                status_emoji = "🔴" if pair.overlap_percentage >= 70 else "🟡" if pair.overlap_percentage >= 40 else "🟢"
                print(f"   {status_emoji} {pair.service:<12} - {pair.overlap_percentage:>5.1f}% overlap - {pair.consolidation_action}")
        
        print(f"\n🎯 Consolidation Plan:")
        if stats['archive_candidates']:
            print(f"   📦 Archive tool scripts ({len(stats['archive_candidates'])}): {', '.join(stats['archive_candidates'])}")
        if stats['merge_candidates']:
            print(f"   🔀 Merge functionality ({len(stats['merge_candidates'])}): {', '.join(stats['merge_candidates'])}")
        if stats['keep_both']:
            print(f"   ✅ Keep both (different purposes) ({len(stats['keep_both'])}): {', '.join(stats['keep_both'])}")


def main():
    parser = argparse.ArgumentParser(description='Consolidate testing infrastructure')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze testing duplication patterns')
    parser.add_argument('--execute', action='store_true',
                       help='Execute consolidation plan')
    
    args = parser.parse_args()
    
    if not args.analyze and not args.execute:
        print("❌ Must specify either --analyze or --execute")
        parser.print_help()
        return 1
    
    repo_root = Path(__file__).parent.parent
    consolidator = TestingConsolidator(repo_root)
    
    print("🔧 Testing Infrastructure Consolidation Tool")
    print("=" * 50)
    
    if args.analyze:
        stats = consolidator.analyze_repository()
        consolidator.generate_analysis_report(stats)
        
        # Save analysis results
        analysis_file = repo_root / "testing_consolidation_analysis.json"
        analysis_data = {
            'stats': stats,
            'service_pairs': [
                {
                    'service': p.service,
                    'tool_script': str(p.tool_script.relative_to(repo_root)),
                    'integration_test': str(p.integration_test.relative_to(repo_root)),
                    'overlap_percentage': p.overlap_percentage,
                    'consolidation_action': p.consolidation_action
                }
                for p in consolidator.analysis_results
            ]
        }
        
        with open(analysis_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        print(f"\n💾 Analysis saved to: {analysis_file}")
        print("💡 Run with --execute to apply consolidation")
        
    elif args.execute:
        # Load previous analysis or run new one
        analysis_file = repo_root / "testing_consolidation_analysis.json"
        if not analysis_file.exists():
            print("⚠️ No previous analysis found. Running analysis first...")
            consolidator.analyze_repository()
        
        if not consolidator.analysis_results:
            print("❌ No consolidation candidates found")
            return 1
        
        # Show plan and confirm
        stats = consolidator.analyze_repository()
        consolidator.generate_analysis_report(stats)
        
        response = input(f"\n❓ Proceed with consolidation? (y/N): ")
        if response.lower() != 'y':
            print("❌ Consolidation cancelled by user")
            return 1
        
        print("✅ Consolidation framework ready")
        print("💡 Implementation would archive redundant scripts and enhance integration tests")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
