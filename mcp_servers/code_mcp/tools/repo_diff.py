"""
Repository Diff and Analysis Tools
Advanced code analysis and diff generation for MCP Code Server
"""

import asyncio
import difflib
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

from loguru import logger

from .github_tools import GitHubTools, GitHubAPIError


class RepoDiffAnalyzer:
    """Advanced repository diff and analysis tools"""
    
    def __init__(self, github_tools: GitHubTools):
        self.github_tools = github_tools
    
    def generate_unified_diff(self, original: str, modified: str, 
                            filename: str = "file", context_lines: int = 3) -> str:
        """Generate unified diff between two file contents"""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            n=context_lines
        )
        
        return ''.join(diff)
    
    def analyze_diff_complexity(self, diff_content: str) -> Dict[str, Any]:
        """Analyze diff complexity and impact"""
        lines = diff_content.split('\n')
        
        stats = {
            "additions": 0,
            "deletions": 0,
            "modifications": 0,
            "files_changed": 0,
            "complexity_score": 0,
            "risk_level": "low"
        }
        
        current_file = None
        
        for line in lines:
            if line.startswith('+++') or line.startswith('---'):
                if line.startswith('+++') and not line.endswith('/dev/null'):
                    stats["files_changed"] += 1
                    current_file = line[4:]
            elif line.startswith('+') and not line.startswith('+++'):
                stats["additions"] += 1
            elif line.startswith('-') and not line.startswith('---'):
                stats["deletions"] += 1
        
        # Calculate complexity score
        total_changes = stats["additions"] + stats["deletions"]
        stats["complexity_score"] = total_changes
        
        # Determine risk level
        if total_changes < 10:
            stats["risk_level"] = "low"
        elif total_changes < 50:
            stats["risk_level"] = "medium"
        elif total_changes < 200:
            stats["risk_level"] = "high"
        else:
            stats["risk_level"] = "critical"
        
        return stats
    
    def extract_code_patterns(self, content: str, file_extension: str = ".py") -> Dict[str, List[str]]:
        """Extract code patterns and structures"""
        patterns = {
            "functions": [],
            "classes": [],
            "imports": [],
            "constants": [],
            "comments": []
        }
        
        if file_extension == ".py":
            # Python patterns
            function_pattern = r'^def\s+(\w+)\s*\('
            class_pattern = r'^class\s+(\w+).*:'
            import_pattern = r'^(?:from\s+\S+\s+)?import\s+(.+)'
            constant_pattern = r'^([A-Z_][A-Z0-9_]*)\s*='
            comment_pattern = r'#\s*(.+)'
            
            for line in content.split('\n'):
                line = line.strip()
                
                if re.match(function_pattern, line):
                    patterns["functions"].append(re.match(function_pattern, line).group(1))
                elif re.match(class_pattern, line):
                    patterns["classes"].append(re.match(class_pattern, line).group(1))
                elif re.match(import_pattern, line):
                    patterns["imports"].append(line)
                elif re.match(constant_pattern, line):
                    patterns["constants"].append(re.match(constant_pattern, line).group(1))
                elif re.match(comment_pattern, line):
                    comment = re.match(comment_pattern, line).group(1)
                    if len(comment) > 10:  # Only meaningful comments
                        patterns["comments"].append(comment)
        
        return patterns
    
    async def analyze_file_changes(self, repository: str, file_path: str, 
                                  original_content: str, new_content: str) -> Dict[str, Any]:
        """Comprehensive analysis of file changes"""
        try:
            # Generate diff
            diff = self.generate_unified_diff(original_content, new_content, file_path)
            
            # Analyze diff complexity
            complexity = self.analyze_diff_complexity(diff)
            
            # Extract code patterns
            file_extension = Path(file_path).suffix
            original_patterns = self.extract_code_patterns(original_content, file_extension)
            new_patterns = self.extract_code_patterns(new_content, file_extension)
            
            # Compare patterns
            pattern_changes = {}
            for pattern_type in original_patterns:
                original_set = set(original_patterns[pattern_type])
                new_set = set(new_patterns[pattern_type])
                
                pattern_changes[pattern_type] = {
                    "added": list(new_set - original_set),
                    "removed": list(original_set - new_set),
                    "unchanged": list(original_set & new_set)
                }
            
            return {
                "file_path": file_path,
                "diff": diff,
                "complexity": complexity,
                "pattern_changes": pattern_changes,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "file_size_change": len(new_content) - len(original_content),
                "line_count_change": len(new_content.split('\n')) - len(original_content.split('\n'))
            }
            
        except Exception as e:
            logger.error(f"Error analyzing file changes for {file_path}: {e}")
            raise
    
    async def propose_code_changes(self, repository: str, file_path: str, 
                                  changes_description: str, current_content: str = None) -> Dict[str, Any]:
        """Propose code changes based on description"""
        try:
            # Get current content if not provided
            if current_content is None:
                file_data = await self.github_tools.read_file_content(repository, file_path)
                current_content = file_data["content"]
            
            # This is a placeholder for AI-powered code generation
            # In a real implementation, this would use an LLM to generate the changes
            proposed_changes = {
                "original_content": current_content,
                "proposed_content": current_content,  # Would be modified by AI
                "change_description": changes_description,
                "confidence_score": 0.8,
                "suggested_commit_message": f"Update {file_path}: {changes_description}",
                "review_notes": [
                    "Please review the proposed changes carefully",
                    "Test the changes in a development environment",
                    "Consider the impact on dependent code"
                ]
            }
            
            # Analyze the proposed changes
            analysis = await self.analyze_file_changes(
                repository, file_path, current_content, proposed_changes["proposed_content"]
            )
            
            proposed_changes["analysis"] = analysis
            
            return proposed_changes
            
        except Exception as e:
            logger.error(f"Error proposing code changes for {file_path}: {e}")
            raise
    
    async def validate_code_syntax(self, content: str, file_extension: str) -> Dict[str, Any]:
        """Validate code syntax"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_extension": file_extension
        }
        
        try:
            if file_extension == ".py":
                # Python syntax validation
                import ast
                try:
                    ast.parse(content)
                    validation_result["valid"] = True
                except SyntaxError as e:
                    validation_result["valid"] = False
                    validation_result["errors"].append({
                        "line": e.lineno,
                        "column": e.offset,
                        "message": e.msg,
                        "type": "SyntaxError"
                    })
            
            elif file_extension in [".js", ".ts"]:
                # Basic JavaScript/TypeScript validation (simplified)
                # In a real implementation, you'd use a proper JS parser
                if "function(" in content and not content.count("(") == content.count(")"):
                    validation_result["warnings"].append({
                        "message": "Potential parentheses mismatch",
                        "type": "Warning"
                    })
            
            elif file_extension in [".json"]:
                # JSON validation
                try:
                    json.loads(content)
                    validation_result["valid"] = True
                except json.JSONDecodeError as e:
                    validation_result["valid"] = False
                    validation_result["errors"].append({
                        "line": e.lineno,
                        "column": e.colno,
                        "message": e.msg,
                        "type": "JSONDecodeError"
                    })
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append({
                "message": f"Validation error: {e}",
                "type": "ValidationError"
            })
        
        return validation_result
    
    async def generate_commit_message(self, changes: List[Dict[str, Any]]) -> str:
        """Generate intelligent commit message based on changes"""
        if not changes:
            return "chore: minor updates"
        
        # Analyze change types
        file_types = set()
        change_types = set()
        
        for change in changes:
            file_path = change.get("file_path", "")
            file_ext = Path(file_path).suffix
            file_types.add(file_ext)
            
            complexity = change.get("analysis", {}).get("complexity", {})
            additions = complexity.get("additions", 0)
            deletions = complexity.get("deletions", 0)
            
            if additions > deletions * 2:
                change_types.add("feat")
            elif deletions > additions * 2:
                change_types.add("refactor")
            else:
                change_types.add("update")
        
        # Generate commit message
        if "feat" in change_types:
            prefix = "feat"
        elif "refactor" in change_types:
            prefix = "refactor"
        else:
            prefix = "update"
        
        if len(file_types) == 1:
            file_type = list(file_types)[0]
            if file_type == ".py":
                scope = "python"
            elif file_type in [".js", ".ts"]:
                scope = "frontend"
            elif file_type in [".md"]:
                scope = "docs"
            else:
                scope = "config"
        else:
            scope = "multiple"
        
        total_files = len(changes)
        
        if total_files == 1:
            file_name = Path(changes[0].get("file_path", "")).name
            message = f"{prefix}({scope}): update {file_name}"
        else:
            message = f"{prefix}({scope}): update {total_files} files"
        
        return message

