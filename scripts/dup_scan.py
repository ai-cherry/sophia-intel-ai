#!/usr/bin/env python3
"""
Semantic Deduplication Scanner
Prevents fragmentation by detecting similar code patterns
"""

import os
import sys
import ast
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple
import difflib
import argparse
from collections import defaultdict

class DuplicationScanner:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.signatures = defaultdict(list)
        self.duplicates = []
        
    def scan_file(self, file_path: Path) -> Dict:
        """Extract signatures from a file"""
        try:
            content = file_path.read_text()
            
            if file_path.suffix == '.py':
                return self.scan_python(file_path, content)
            elif file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
                return self.scan_javascript(file_path, content)
            else:
                return self.scan_generic(file_path, content)
                
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
            return {}
    
    def scan_python(self, file_path: Path, content: str) -> Dict:
        """Extract Python function/class signatures"""
        signatures = {}
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    sig = self.get_function_signature(node)
                    signatures[sig] = {
                        'type': 'function',
                        'name': node.name,
                        'file': str(file_path),
                        'line': node.lineno
                    }
                elif isinstance(node, ast.ClassDef):
                    sig = self.get_class_signature(node)
                    signatures[sig] = {
                        'type': 'class',
                        'name': node.name,
                        'file': str(file_path),
                        'line': node.lineno
                    }
        except:
            pass
            
        return signatures
    
    def scan_javascript(self, file_path: Path, content: str) -> Dict:
        """Extract JavaScript/TypeScript function/class signatures"""
        signatures = {}
        
        # Simple regex-based extraction
        import re
        
        # Functions
        func_pattern = r'(?:function|const|let|var)\s+(\w+)\s*(?:=\s*)?(?:\([^)]*\)|<[^>]*>)*\s*(?:=>|\{)'
        for match in re.finditer(func_pattern, content):
            name = match.group(1)
            sig = f"function:{name}"
            signatures[sig] = {
                'type': 'function',
                'name': name,
                'file': str(file_path),
                'line': content[:match.start()].count('\n') + 1
            }
        
        # Classes
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            name = match.group(1)
            sig = f"class:{name}"
            signatures[sig] = {
                'type': 'class',
                'name': name,
                'file': str(file_path),
                'line': content[:match.start()].count('\n') + 1
            }
        
        # React components
        component_pattern = r'(?:export\s+)?(?:default\s+)?(?:function|const)\s+([A-Z]\w+)'
        for match in re.finditer(component_pattern, content):
            name = match.group(1)
            sig = f"component:{name}"
            signatures[sig] = {
                'type': 'component',
                'name': name,
                'file': str(file_path),
                'line': content[:match.start()].count('\n') + 1
            }
        
        return signatures
    
    def scan_generic(self, file_path: Path, content: str) -> Dict:
        """Generic text similarity check"""
        # Create content hash for exact duplicates
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        return {
            content_hash: {
                'type': 'file',
                'name': file_path.name,
                'file': str(file_path),
                'line': 1
            }
        }
    
    def get_function_signature(self, node: ast.FunctionDef) -> str:
        """Generate a signature for a Python function"""
        args = [arg.arg for arg in node.args.args]
        return f"function:{node.name}:{','.join(args)}"
    
    def get_class_signature(self, node: ast.ClassDef) -> str:
        """Generate a signature for a Python class"""
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        return f"class:{node.name}:{','.join(methods[:3])}"
    
    def scan_directory(self, directory: Path, ignore_dirs: Set[str] = None):
        """Scan all files in a directory"""
        ignore_dirs = ignore_dirs or {'node_modules', '.git', '__pycache__', 'venv', '.venv'}
        
        for root, dirs, files in os.walk(directory):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                if file.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
                    file_path = Path(root) / file
                    signatures = self.scan_file(file_path)
                    
                    # Store signatures for comparison
                    for sig, info in signatures.items():
                        self.signatures[sig].append(info)
    
    def find_duplicates(self) -> List[Dict]:
        """Find all duplicate signatures"""
        duplicates = []
        
        for sig, locations in self.signatures.items():
            if len(locations) > 1:
                duplicates.append({
                    'signature': sig,
                    'count': len(locations),
                    'locations': locations
                })
        
        return duplicates
    
    def check_similarity(self, file1: Path, file2: Path, threshold: float = 0.8) -> float:
        """Check similarity between two files"""
        try:
            content1 = file1.read_text()
            content2 = file2.read_text()
            
            # Use difflib for similarity ratio
            similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
            
            return similarity
        except:
            return 0.0
    
    def scan_branch(self, branch: str) -> Dict:
        """Scan changes in a branch for duplicates"""
        import subprocess
        
        # Get changed files in branch
        result = subprocess.run(
            ['git', 'diff', f'main...{branch}', '--name-only'],
            capture_output=True,
            text=True
        )
        
        changed_files = result.stdout.strip().split('\n')
        
        report = {
            'branch': branch,
            'changed_files': changed_files,
            'duplicates': [],
            'similar_files': []
        }
        
        # Check each changed file for duplicates
        for file in changed_files:
            if not file:
                continue
                
            file_path = self.repo_root / file
            if not file_path.exists():
                continue
            
            # Get signatures from this file
            signatures = self.scan_file(file_path)
            
            # Check against existing codebase
            for sig, info in signatures.items():
                if sig in self.signatures and len(self.signatures[sig]) > 0:
                    # Found potential duplicate
                    existing = self.signatures[sig][0]
                    if existing['file'] != str(file_path):
                        report['duplicates'].append({
                            'new': info,
                            'existing': existing,
                            'signature': sig
                        })
            
            # Check for similar files
            for existing_file in self.repo_root.rglob(f"*{file_path.suffix}"):
                if existing_file == file_path:
                    continue
                    
                similarity = self.check_similarity(file_path, existing_file)
                if similarity > 0.8:
                    report['similar_files'].append({
                        'new': str(file_path),
                        'existing': str(existing_file),
                        'similarity': f"{similarity:.2%}"
                    })
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Scan for code duplicates')
    parser.add_argument('--branch', help='Check specific branch for duplicates')
    parser.add_argument('--full', action='store_true', help='Full repository scan')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()
    
    repo_root = Path.cwd()
    scanner = DuplicationScanner(repo_root)
    
    if args.branch:
        # Scan main repository first
        print("📊 Scanning main repository...")
        scanner.scan_directory(repo_root)
        
        # Check branch for duplicates
        print(f"🔍 Checking branch '{args.branch}' for duplicates...")
        report = scanner.scan_branch(args.branch)
        
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            # Pretty print report
            print("\n" + "="*60)
            print(f"DUPLICATION REPORT FOR BRANCH: {args.branch}")
            print("="*60)
            
            if report['duplicates']:
                print(f"\n❌ Found {len(report['duplicates'])} potential duplicates:")
                for dup in report['duplicates']:
                    print(f"\n  Duplicate {dup['new']['type']}: {dup['new']['name']}")
                    print(f"    New: {dup['new']['file']}:{dup['new']['line']}")
                    print(f"    Existing: {dup['existing']['file']}:{dup['existing']['line']}")
            else:
                print("\n✅ No exact duplicates found")
            
            if report['similar_files']:
                print(f"\n⚠️  Found {len(report['similar_files'])} similar files:")
                for sim in report['similar_files']:
                    print(f"\n  Files with {sim['similarity']} similarity:")
                    print(f"    New: {sim['new']}")
                    print(f"    Existing: {sim['existing']}")
            else:
                print("\n✅ No highly similar files found")
            
            # Summary
            print("\n" + "="*60)
            if not report['duplicates'] and not report['similar_files']:
                print("✅ SAFE TO MERGE - No duplicates detected")
            else:
                print("⚠️  REVIEW REQUIRED - Potential duplicates found")
            print("="*60)
    
    elif args.full:
        print("📊 Running full repository scan...")
        scanner.scan_directory(repo_root)
        duplicates = scanner.find_duplicates()
        
        if args.json:
            print(json.dumps(duplicates, indent=2))
        else:
            print(f"\nFound {len(duplicates)} duplicate signatures:")
            for dup in duplicates[:10]:  # Show first 10
                print(f"\n  {dup['signature']} appears {dup['count']} times:")
                for loc in dup['locations']:
                    print(f"    - {loc['file']}:{loc['line']}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()