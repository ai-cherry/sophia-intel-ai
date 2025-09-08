#!/usr/bin/env python3
"""
Syntax Error Detection and Analysis Tool
Part of the Black Formatting Remediation Plan

This script identifies and categorizes Python syntax errors
to help prioritize fixes for the 42 files that Black cannot format.
"""

import ast
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import json

class SyntaxErrorDetector:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.failed_files = []
        self.error_categories = {
            'regex_patterns': [],
            'docstring_issues': [],
            'incomplete_strings': [],
            'function_definitions': [],
            'missing_content': [],
            'other': []
        }
        
    def get_black_failed_files(self) -> List[str]:
        """Get list of files that Black cannot format"""
        try:
            result = subprocess.run(
                ['black', '--check', '.'],
                capture_output=True,
                text=True,
                cwd=self.root_dir
            )
            
            failed_files = []
            for line in result.stderr.split('\n'):
                if 'cannot format' in line and ':' in line:
                    # Extract file path from error line
                    parts = line.split(':')
                    if len(parts) >= 2:
                        file_path = parts[0].replace('error: cannot format ', '').strip()
                        failed_files.append(file_path)
                        
            return list(set(failed_files))  # Remove duplicates
            
        except subprocess.CalledProcessError as e:
            print(f"Error running Black: {e}")
            return []
        except FileNotFoundError:
            print("Black is not installed or not in PATH")
            return []
    
    def check_syntax_error(self, file_path: Path) -> Optional[Dict]:
        """Check if a Python file has syntax errors and categorize them"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return {
                'file': str(file_path),
                'error_type': 'file_read_error',
                'message': str(e),
                'line': None,
                'content_preview': None
            }
        
        try:
            ast.parse(content)
            return None  # No syntax error
        except SyntaxError as e:
            error_info = {
                'file': str(file_path),
                'error_type': 'syntax_error',
                'message': e.msg,
                'line': e.lineno,
                'offset': e.offset,
                'text': e.text.strip() if e.text else None,
                'content_preview': self.get_content_preview(content, e.lineno)
            }
            
            # Categorize the error
            error_info['category'] = self.categorize_error(content, e, file_path)
            return error_info
        except Exception as e:
            return {
                'file': str(file_path),
                'error_type': 'other_error',
                'message': str(e),
                'line': None,
                'content_preview': None,
                'category': 'other'
            }
    
    def categorize_error(self, content: str, error: SyntaxError, file_path: Path) -> str:
        """Categorize the type of syntax error"""
        error_text = error.text.strip() if error.text else ""
        error_msg = error.msg.lower() if error.msg else ""
        
        # Check for regex pattern issues
        if "r'" in error_text and 'r\'\\b' in content:
            return 'regex_patterns'
        
        # Check for docstring issues
        if '"""' in error_text or "'''" in error_text:
            return 'docstring_issues'
        
        # Check for incomplete strings
        if 'unterminated string' in error_msg or '"' in error_text:
            return 'incomplete_strings'
        
        # Check for function definition issues
        if ('def ' in error_text or 'async def' in error_text or 
            'invalid syntax' in error_msg and ':' in error_text):
            return 'function_definitions'
        
        # Check for missing content issues
        if 'unexpected EOF' in error_msg or 'line number missing' in str(error):
            return 'missing_content'
        
        return 'other'
    
    def get_content_preview(self, content: str, error_line: int, context_lines: int = 3) -> Dict:
        """Get preview of content around the error line"""
        lines = content.split('\n')
        start = max(0, error_line - context_lines - 1)
        end = min(len(lines), error_line + context_lines)
        
        preview_lines = []
        for i in range(start, end):
            marker = " ❌ " if i == error_line - 1 else "    "
            preview_lines.append(f"{i+1:3d}{marker}{lines[i]}")
        
        return {
            'lines': preview_lines,
            'error_line': error_line,
            'start_line': start + 1,
            'end_line': end
        }
    
    def analyze_all_errors(self) -> Dict:
        """Analyze all syntax errors in the project"""
        print("🔍 Getting list of files that Black cannot format...")
        failed_files = self.get_black_failed_files()
        
        if not failed_files:
            print("✅ No files found that Black cannot format!")
            return {'errors': [], 'summary': {}}
        
        print(f"📝 Found {len(failed_files)} files with issues. Analyzing syntax errors...")
        
        errors = []
        category_counts = {}
        
        for file_path_str in failed_files:
            file_path = Path(file_path_str)
            if not file_path.exists():
                continue
                
            error_info = self.check_syntax_error(file_path)
            if error_info:
                errors.append(error_info)
                category = error_info.get('category', 'other')
                category_counts[category] = category_counts.get(category, 0) + 1
        
        summary = {
            'total_files': len(failed_files),
            'files_with_syntax_errors': len(errors),
            'category_breakdown': category_counts
        }
        
        return {
            'errors': errors,
            'summary': summary,
            'failed_files': failed_files
        }
    
    def generate_report(self, analysis: Dict) -> str:
        """Generate a detailed report of syntax errors"""
        errors = analysis['errors']
        summary = analysis['summary']
        
        report = []
        report.append("🔧 SOPHIA INTEL AI - SYNTAX ERROR ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")
        report.append(f"📊 SUMMARY:")
        report.append(f"  • Total files Black cannot format: {summary['total_files']}")
        report.append(f"  • Files with syntax errors: {summary['files_with_syntax_errors']}")
        report.append("")
        
        report.append("📈 ERROR CATEGORIES:")
        for category, count in summary['category_breakdown'].items():
            report.append(f"  • {category.replace('_', ' ').title()}: {count} files")
        report.append("")
        
        # Group errors by category
        by_category = {}
        for error in errors:
            category = error.get('category', 'other')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(error)
        
        # Report each category
        priority_order = [
            'missing_content', 'regex_patterns', 'function_definitions',
            'docstring_issues', 'incomplete_strings', 'other'
        ]
        
        for category in priority_order:
            if category not in by_category:
                continue
                
            report.append(f"🚨 {category.replace('_', ' ').upper()} ERRORS ({len(by_category[category])} files):")
            report.append("-" * 50)
            
            for error in by_category[category][:5]:  # Show first 5 of each category
                report.append(f"\n📁 File: {error['file']}")
                if error.get('line'):
                    report.append(f"📍 Line: {error['line']}")
                report.append(f"💬 Error: {error['message']}")
                
                if error.get('text'):
                    report.append(f"🔍 Problem text: {error['text']}")
                
                if error.get('content_preview'):
                    report.append("📄 Context:")
                    for line in error['content_preview']['lines']:
                        report.append(f"    {line}")
                
                report.append("")
            
            if len(by_category[category]) > 5:
                report.append(f"    ... and {len(by_category[category]) - 5} more files")
            
            report.append("")
        
        return "\n".join(report)
    
    def save_failed_files_list(self, failed_files: List[str]):
        """Save the list of failed files for other scripts to use"""
        failed_files_path = self.root_dir / 'failed_files.txt'
        with open(failed_files_path, 'w') as f:
            for file_path in sorted(failed_files):
                f.write(file_path + '\n')
        
        print(f"💾 Saved failed files list to: {failed_files_path}")
    
    def run_analysis(self):
        """Run the complete syntax error analysis"""
        print("🚀 Starting syntax error analysis...")
        
        analysis = self.analyze_all_errors()
        
        if not analysis['errors']:
            print("✅ No syntax errors found in Black-failed files!")
            return
        
        # Generate and save report
        report = self.generate_report(analysis)
        
        report_path = self.root_dir / 'SYNTAX_ERROR_ANALYSIS_REPORT.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        print(f"\n💾 Full report saved to: {report_path}")
        
        # Save failed files list
        self.save_failed_files_list(analysis['failed_files'])
        
        # Save detailed JSON data
        json_path = self.root_dir / 'syntax_errors_detailed.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"💾 Detailed data saved to: {json_path}")
        
        # Show next steps
        print("\n🎯 NEXT STEPS:")
        print("1. Review the generated reports")
        print("2. Start with 'missing_content' category (highest priority)")
        print("3. Use the syntax_fixer.py script for automated fixes")
        print("4. Run 'python -m py_compile <file>' to test fixes")
        print("5. Run 'black <file>' after each fix to verify formatting")

def main():
    """Main execution function"""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = "."
    
    detector = SyntaxErrorDetector(root_dir)
    detector.run_analysis()

if __name__ == "__main__":
    main()
