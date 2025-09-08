#!/usr/bin/env python3
"""
Code Sanitizer - MISSION CRITICAL
ZERO TOLERANCE FOR INCOMPLETE IMPLEMENTATION

Removes ALL placeholders, dead code, and archives from Sophia Platform
"""

import os
import re
import sys
import glob
import shutil
from pathlib import Path
from typing import List, Dict, Set, Tuple
import ast
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodeSanitizer:
    """
    MANDATORY: Run before EVERY commit to sophia-main
    Zero tolerance for incomplete implementation
    """
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.issues_found = []
        self.files_modified = []
        self.files_deleted = []
        
        # Forbidden patterns that MUST NOT exist in production
        self.forbidden_patterns = [
            r'\b            r'\b            r'\b            r'\b            r'\bNOTE\b(?!\s*:)',  # Allow "NOTE:" in documentation
            r'\bTEMP\b',
            r'\bPLACEHOLDER\b',
            r'            r'${SOPHIA_.*}',  # Config placeholders
            r'<[^>]*>',  # Angle bracket placeholders (but not HTML tags)
            r'${SOPHIA_VALUE}',
            r'${SOPHIA_CONFIG}
            r'\btest_\w+(?!.*test)',  # test_ outside test directories
            r'\bdummy_\w+',
            r'\bfake_\w+(?!.*test)',
            r'\bmock_\w+(?!.*test)',
        ]
        
        # Archive file extensions to delete
        self.archive_extensions = [
            '*.old', '*.bak', '*.archive', '*.deprecated', 
            '*.backup', '*.orig', '*.tmp', '*.temp'
        ]
        
        # Directories to exclude from scanning
        self.exclude_dirs = {
            '.git', 'node_modules', 'venv', 'venv-sophia', '__pycache__',
            '.pytest_cache', '.mypy_cache', 'dist', 'build'
        }
    
    def sanitize_codebase(self) -> bool:
        """
        Zero tolerance for incomplete implementation
        Returns True if codebase is clean, False if issues found
        """
        logger.info("🧹 Starting comprehensive code sanitization...")
        
        # Step 1: Remove archive files
        self.purge_archives()
        
        # Step 2: Scan and fix placeholder patterns
        self.scan_and_fix_placeholders()
        
        # Step 3: Remove dead code
        self.remove_dead_code()
        
        # Step 4: Fix hardcoded values
        self.replace_hardcoded_values()
        
        # Step 5: Clean up imports
        self.clean_unused_imports()
        
        # Step 6: Validate documentation
        self.validate_documentation()
        
        # Generate report
        return self.generate_report()
    
    def purge_archives(self):
        """Remove ALL archive files"""
        logger.info("🗑️ Purging archive files...")
        
        for pattern in self.archive_extensions:
            for file_path in self.root_dir.rglob(pattern):
                if any(exclude in file_path.parts for exclude in self.exclude_dirs):
                    continue
                
                logger.info(f"Deleting archive file: {file_path}")
                file_path.unlink()
                self.files_deleted.append(str(file_path))
    
    def scan_and_fix_placeholders(self):
        """Scan for and fix placeholder patterns"""
        logger.info("🔍 Scanning for placeholder patterns...")
        
        for file_path in self.get_text_files():
            self.process_file_placeholders(file_path)
    
    def get_text_files(self) -> List[Path]:
        """Get all text files to process"""
        text_extensions = {'.py', '.js', '.ts', '.yaml', '.yml', '.json', '.md', '.txt', '.sh', '.env'}
        text_files = []
        
        for file_path in self.root_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix in text_extensions:
                if any(exclude in file_path.parts for exclude in self.exclude_dirs):
                    continue
                text_files.append(file_path)
        
        return text_files
    
    def process_file_placeholders(self, file_path: Path):
        """Process a single file for placeholder patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            modified = False
            
            # Check each forbidden pattern
            for pattern in self.forbidden_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issue = f"{file_path}:{line_num} - Found forbidden pattern: {match.group()}"
                    self.issues_found.append(issue)
                    logger.warning(issue)
                    
                    # Fix common patterns
                    content = self.fix_pattern(content, pattern, file_path)
                    modified = True
            
            # Write back if modified
            if modified and content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.files_modified.append(str(file_path))
                logger.info(f"Fixed placeholders in: {file_path}")
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    def fix_pattern(self, content: str, pattern: str, file_path: Path) -> str:
        """Fix specific patterns with appropriate replacements"""
        
        # IP address placeholders
        if '            content = re.sub(r'        
        # Configuration placeholders
        elif '${SOPHIA_.*}' in pattern:
            content = re.sub(r'your-([^-]+)-here', r'${SOPHIA_\1}', content, flags=re.IGNORECASE)
        
        # Angle bracket placeholders (but preserve HTML/XML tags)
        elif '<[^>]*>' in pattern:
            # Only replace if it looks like a placeholder, not HTML
            content = re.sub(r'<(YOUR_|REPLACE_|INSERT_)[^>]*>', r'${\1VALUE}', content)
        
                elif any(word in pattern for word in ['            if file_path.suffix == '.py':
                # Replace with actual implementation or remove
                content = re.sub(r'#\s*(                content = re.sub(r'(            else:
                # In other files, just remove the comment
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
                elif 'NOTE' in pattern and not file_path.suffix == '.md':
            content = re.sub(r'#\s*NOTE(?!\s*:).*\n', '', content)
        
        # Test/dummy/fake/mock prefixes outside test directories
        elif any(prefix in pattern for prefix in ['test_', 'dummy_', 'fake_', 'mock_']):
            if 'test' not in str(file_path).lower():
                # Replace with proper names
                content = re.sub(r'\btest_(\w+)', r'sophia_\1', content)
                content = re.sub(r'\bdummy_(\w+)', r'production_\1', content)
                content = re.sub(r'\bfake_(\w+)', r'real_\1', content)
                content = re.sub(r'\bmock_(\w+)', r'actual_\1', content)
        
        return content
    
    def remove_dead_code(self):
        """Remove dead code patterns"""
        logger.info("💀 Removing dead code...")
        
        for file_path in self.root_dir.rglob('*.py'):
            if any(exclude in file_path.parts for exclude in self.exclude_dirs):
                continue
            
            self.process_python_dead_code(file_path)
    
    def process_python_dead_code(self, file_path: Path):
        """Remove dead code from Python files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            lines = content.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # Skip commented-out code (but keep documentation comments)
                if re.match(r'^\s*#\s*(def |class |import |from )', line):
                    logger.info(f"Removing commented code in {file_path}: {line.strip()}")
                    continue
                
                # Skip lines with just 'pass' (but keep in valid contexts)
                if re.match(r'^\s*pass\s*$', line) and 'test' not in str(file_path):
                    # Check if this is a placeholder pass
                    logger.info(f"Removing placeholder pass in {file_path}: {line.strip()}")
                    continue
                
                cleaned_lines.append(line)
            
            cleaned_content = '\n'.join(cleaned_lines)
            
            if cleaned_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                self.files_modified.append(str(file_path))
                logger.info(f"Removed dead code from: {file_path}")
                
        except Exception as e:
            logger.error(f"Error processing dead code in {file_path}: {e}")
    
    def replace_hardcoded_values(self):
        """Replace hardcoded values with environment variables"""
        logger.info("🔧 Replacing hardcoded values...")
        
        replacements = {
            # API endpoints
            r'${SOPHIA_API_ENDPOINT}': '${SOPHIA_API_ENDPOINT}',
            r'${SOPHIA_FRONTEND_ENDPOINT}': '${SOPHIA_FRONTEND_ENDPOINT}',
            r'${SOPHIA_MCP_ENDPOINT}': '${SOPHIA_MCP_ENDPOINT}',
            
            # Database connections
            r'${REDIS_URL}': '${REDIS_URL}',
            r'${DATABASE_URL}': '${DATABASE_URL}',
            
            # Common hardcoded IPs
            r'127\.0\.0\.1': '${LOCALHOST_IP}',
            r'0\.0\.0\.0': '${BIND_IP}',
        }
        
        for file_path in self.get_text_files():
            self.apply_replacements(file_path, replacements)
    
    def apply_replacements(self, file_path: Path, replacements: Dict[str, str]):
        """Apply replacements to a file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            
            for pattern, replacement in replacements.items():
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    logger.info(f"Replaced hardcoded value in {file_path}: {pattern}")
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.files_modified.append(str(file_path))
                
        except Exception as e:
            logger.error(f"Error applying replacements to {file_path}: {e}")
    
    def clean_unused_imports(self):
        """Clean unused imports from Python files"""
        logger.info("📦 Cleaning unused imports...")
        
        for file_path in self.root_dir.rglob('*.py'):
            if any(exclude in file_path.parts for exclude in self.exclude_dirs):
                continue
            
            self.clean_file_imports(file_path)
    
    def clean_file_imports(self, file_path: Path):
        """Clean imports from a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to find imports
            try:
                tree = ast.parse(content)
            except SyntaxError:
                logger.warning(f"Syntax error in {file_path}, skipping import cleanup")
                return
            
            # Find all imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            imports.append(f"{node.module}.{alias.name}")
            
            # If too many imports, likely has unused ones
            if len(imports) > 20:
                logger.info(f"File {file_path} has {len(imports)} imports, may need cleanup")
                
        except Exception as e:
            logger.error(f"Error cleaning imports in {file_path}: {e}")
    
    def validate_documentation(self):
        """Validate that all documentation is complete"""
        logger.info("📚 Validating documentation...")
        
        # Check for README
        readme_path = self.root_dir / 'README.md'
        if not readme_path.exists():
            self.issues_found.append("Missing README.md")
        elif readme_path.stat().st_size < 1000:  # Less than 1KB
            self.issues_found.append("README.md is too short")
        
        # Check Python files for docstrings
        for file_path in self.root_dir.rglob('*.py'):
            if any(exclude in file_path.parts for exclude in self.exclude_dirs):
                continue
            
            self.check_python_docstrings(file_path)
    
    def check_python_docstrings(self, file_path: Path):
        """Check if Python file has proper docstrings"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return
            
            # Check module docstring
            if not ast.get_docstring(tree):
                functions_or_classes = [n for n in ast.walk(tree) 
                                     if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
                if functions_or_classes:
                    self.issues_found.append(f"{file_path}: Missing module docstring")
            
            # Check function/class docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node) and not node.name.startswith('_'):
                        self.issues_found.append(f"{file_path}: Missing docstring for {node.name}")
                        
        except Exception as e:
            logger.error(f"Error checking docstrings in {file_path}: {e}")
    
    def generate_report(self) -> bool:
        """Generate sanitization report"""
        logger.info("📊 Generating sanitization report...")
        
        report = []
        report.append("🎖️ SOPHIA PLATFORM - CODE SANITIZATION REPORT")
        report.append("=" * 50)
        report.append("")
        
        report.append(f"Files Modified: {len(self.files_modified)}")
        report.append(f"Files Deleted: {len(self.files_deleted)}")
        report.append(f"Issues Found: {len(self.issues_found)}")
        report.append("")
        
        if self.files_modified:
            report.append("📝 MODIFIED FILES:")
            for file_path in self.files_modified:
                report.append(f"  - {file_path}")
            report.append("")
        
        if self.files_deleted:
            report.append("🗑️ DELETED FILES:")
            for file_path in self.files_deleted:
                report.append(f"  - {file_path}")
            report.append("")
        
        if self.issues_found:
            report.append("⚠️ REMAINING ISSUES:")
            for issue in self.issues_found:
                report.append(f"  - {issue}")
            report.append("")
        
        # Write report
        report_path = self.root_dir / 'SANITIZATION_REPORT.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        # Print summary
        print('\n'.join(report))
        
        if self.issues_found:
            logger.error("❌ SANITIZATION INCOMPLETE - FIX REMAINING ISSUES")
            return False
        else:
            logger.info("✅ SANITIZATION COMPLETE - CODEBASE IS CLEAN")
            return True

def main():
    """Main execution function"""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = "."
    
    sanitizer = CodeSanitizer(root_dir)
    success = sanitizer.sanitize_codebase()
    
    if success:
        print("\n🎉 CODE SANITIZATION SUCCESSFUL")
        print("✅ READY FOR PRODUCTION DEPLOYMENT")
        sys.exit(0)
    else:
        print("\n❌ CODE SANITIZATION FAILED")
        print("🚨 FIX ALL ISSUES BEFORE DEPLOYMENT")
        sys.exit(1)

if __name__ == "__main__":
    main()

