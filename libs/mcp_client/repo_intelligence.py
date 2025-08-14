"""
Enhanced Repository Intelligence
Integrates with MCP servers for comprehensive repository analysis and semantic search
"""

import asyncio
import json
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
import logging
import hashlib
import re

from .sophia_client import SophiaMCPClient, MCPServerError

logger = logging.getLogger(__name__)


class RepositoryIntelligence:
    """
    Enhanced repository intelligence that provides semantic code search,
    pattern recognition, and architectural analysis using MCP servers.
    """

    def __init__(self, 
                 mcp_client: SophiaMCPClient,
                 repo_root: Optional[str] = None):
        self.mcp_client = mcp_client
        self.repo_root = Path(repo_root) if repo_root else Path.cwd()
        self.index_cache = {}
        self.pattern_cache = {}
        
        # File type mappings for intelligent analysis
        self.language_extensions = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }

    async def index_repository(self, 
                             force_refresh: bool = False,
                             include_docs: bool = True,
                             include_tests: bool = True) -> Dict[str, Any]:
        """
        Index the entire repository for semantic search and analysis
        
        Args:
            force_refresh: Force a complete re-index
            include_docs: Include documentation files
            include_tests: Include test files
            
        Returns:
            Indexing summary and statistics
        """
        start_time = time.time()
        logger.info(f"Starting repository indexing for {self.repo_root}")
        
        try:
            # Get repository structure
            repo_structure = await self._analyze_repo_structure()
            
            # Index source code files
            code_files = await self._find_source_files(include_tests)
            code_index_stats = await self._index_source_files(code_files, force_refresh)
            
            # Index documentation if requested
            docs_stats = {}
            if include_docs:
                docs_files = await self._find_documentation_files()
                docs_stats = await self._index_documentation(docs_files, force_refresh)
            
            # Analyze code patterns and architecture
            pattern_analysis = await self._analyze_code_patterns(code_files)
            
            # Store repository metadata
            repo_metadata = {
                "repo_root": str(self.repo_root),
                "indexed_at": datetime.now().isoformat(),
                "structure": repo_structure,
                "code_stats": code_index_stats,
                "docs_stats": docs_stats,
                "pattern_analysis": pattern_analysis,
                "indexing_duration": time.time() - start_time
            }
            
            await self.mcp_client.store_context(
                content=json.dumps(repo_metadata, default=str),
                context_type="repo_index",
                metadata={
                    "repo_root": str(self.repo_root),
                    "total_files": code_index_stats.get("files_indexed", 0),
                    "languages": list(repo_structure.get("languages", {}).keys())
                }
            )
            
            logger.info(f"Repository indexing completed in {time.time() - start_time:.2f}s")
            return repo_metadata
            
        except Exception as e:
            logger.error(f"Repository indexing failed: {e}")
            raise

    async def semantic_code_search(self, 
                                 query: str,
                                 language: Optional[str] = None,
                                 file_patterns: Optional[List[str]] = None,
                                 max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform semantic search across the codebase
        
        Args:
            query: Search query (natural language or code)
            language: Optional language filter
            file_patterns: Optional file pattern filters
            max_results: Maximum number of results
            
        Returns:
            List of relevant code matches with context
        """
        try:
            # Build enhanced query
            enhanced_query = self._build_semantic_query(query, language, file_patterns)
            
            # Search using MCP client
            results = await self.mcp_client.query_context(
                query=enhanced_query,
                top_k=max_results,
                threshold=0.6,
                context_types=["code_index", "function_definition", "class_definition"]
            )
            
            # Enhance results with additional context
            enhanced_results = []
            for result in results:
                enhanced_result = await self._enhance_search_result(result)
                enhanced_results.append(enhanced_result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Semantic code search failed: {e}")
            return []

    async def find_similar_code(self, 
                              code_snippet: str,
                              language: Optional[str] = None,
                              similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find code similar to the provided snippet
        
        Args:
            code_snippet: Code snippet to find similarities for
            language: Optional language filter
            similarity_threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of similar code locations
        """
        try:
            # Extract key features from code snippet
            features = self._extract_code_features(code_snippet, language)
            
            # Build search query from features
            feature_query = " ".join([
                f"function:{feat}" if feat.startswith("def ") or feat.startswith("function ")
                else f"pattern:{feat}"
                for feat in features[:5]  # Use top 5 features
            ])
            
            results = await self.mcp_client.query_context(
                query=feature_query,
                top_k=15,
                threshold=similarity_threshold,
                context_types=["code_index"]
            )
            
            # Filter and rank results by actual code similarity
            similar_results = []
            for result in results:
                similarity_score = self._calculate_code_similarity(
                    code_snippet, result.get("content", "")
                )
                
                if similarity_score >= similarity_threshold:
                    result["similarity_score"] = similarity_score
                    similar_results.append(result)
            
            # Sort by similarity score
            similar_results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            
            return similar_results
            
        except Exception as e:
            logger.error(f"Similar code search failed: {e}")
            return []

    async def analyze_dependencies(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze dependencies and relationships for a specific file
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dependency analysis results
        """
        try:
            file_path_obj = Path(file_path)
            
            # Get file content for analysis
            if not file_path_obj.exists():
                return {"error": f"File not found: {file_path}"}
            
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Analyze imports and dependencies
            dependencies = self._extract_dependencies(content, file_path_obj.suffix)
            
            # Find files that depend on this file
            dependents = await self._find_dependents(file_path)
            
            # Get related files based on patterns
            related_files = await self._find_related_files(file_path, content)
            
            analysis = {
                "file_path": file_path,
                "dependencies": dependencies,
                "dependents": dependents,
                "related_files": related_files,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Store dependency analysis
            await self.mcp_client.store_context(
                content=json.dumps(analysis, default=str),
                context_type="dependency_analysis",
                metadata={
                    "file_path": file_path,
                    "dependency_count": len(dependencies),
                    "dependent_count": len(dependents)
                }
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Dependency analysis failed for {file_path}: {e}")
            return {"error": str(e), "file_path": file_path}

    async def get_architectural_insights(self) -> Dict[str, Any]:
        """
        Get architectural insights about the repository
        
        Returns:
            Architectural analysis and recommendations
        """
        try:
            # Query for architectural patterns
            patterns = await self.mcp_client.query_context(
                query="architecture pattern structure design",
                top_k=20,
                threshold=0.5,
                context_types=["code_index", "repo_index"]
            )
            
            # Analyze common patterns
            insights = {
                "common_patterns": self._analyze_architectural_patterns(patterns),
                "complexity_metrics": await self._calculate_complexity_metrics(),
                "hotspots": await self._identify_hotspots(),
                "recommendations": await self._generate_recommendations(),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Architectural analysis failed: {e}")
            return {"error": str(e)}

    async def _analyze_repo_structure(self) -> Dict[str, Any]:
        """Analyze the repository structure and organization"""
        structure = {
            "directories": {},
            "file_types": {},
            "languages": {},
            "total_files": 0,
            "total_lines": 0
        }
        
        for item in self.repo_root.rglob("*"):
            if item.is_file() and not self._should_ignore_file(item):
                # Update file type counts
                suffix = item.suffix.lower()
                structure["file_types"][suffix] = structure["file_types"].get(suffix, 0) + 1
                
                # Update language counts
                language = self.language_extensions.get(suffix, "other")
                structure["languages"][language] = structure["languages"].get(language, 0) + 1
                
                # Update directory structure
                rel_path = item.relative_to(self.repo_root)
                dir_path = str(rel_path.parent)
                if dir_path not in structure["directories"]:
                    structure["directories"][dir_path] = {"files": 0, "size": 0}
                
                structure["directories"][dir_path]["files"] += 1
                structure["directories"][dir_path]["size"] += item.stat().st_size
                
                structure["total_files"] += 1
                
                # Count lines for text files
                if suffix in ['.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.h']:
                    try:
                        with open(item, 'r', encoding='utf-8') as f:
                            lines = sum(1 for _ in f)
                            structure["total_lines"] += lines
                    except (UnicodeDecodeError, PermissionError):
                        pass
        
        return structure

    async def _find_source_files(self, include_tests: bool = True) -> List[Path]:
        """Find all source code files in the repository"""
        source_files = []
        
        for ext in self.language_extensions.keys():
            files = list(self.repo_root.rglob(f"*{ext}"))
            for file in files:
                if self._should_ignore_file(file):
                    continue
                
                if not include_tests and self._is_test_file(file):
                    continue
                
                source_files.append(file)
        
        return source_files

    async def _find_documentation_files(self) -> List[Path]:
        """Find documentation files in the repository"""
        doc_patterns = ["*.md", "*.rst", "*.txt", "*.doc"]
        doc_files = []
        
        for pattern in doc_patterns:
            files = list(self.repo_root.rglob(pattern))
            for file in files:
                if not self._should_ignore_file(file):
                    doc_files.append(file)
        
        return doc_files

    async def _index_source_files(self, files: List[Path], force_refresh: bool) -> Dict[str, Any]:
        """Index source code files"""
        indexed_count = 0
        failed_count = 0
        
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract functions, classes, and key structures
                structures = self._extract_code_structures(content, file.suffix)
                
                # Index file content
                await self.mcp_client.store_context(
                    content=content,
                    context_type="code_index",
                    metadata={
                        "file_path": str(file.relative_to(self.repo_root)),
                        "language": self.language_extensions.get(file.suffix, "other"),
                        "file_size": len(content),
                        "structures": structures
                    }
                )
                
                # Index individual structures
                for structure in structures:
                    await self.mcp_client.store_context(
                        content=structure["code"],
                        context_type=f"{structure['type']}_definition",
                        metadata={
                            "file_path": str(file.relative_to(self.repo_root)),
                            "structure_name": structure["name"],
                            "structure_type": structure["type"],
                            "line_number": structure.get("line", 0)
                        }
                    )
                
                indexed_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to index {file}: {e}")
                failed_count += 1
        
        return {
            "files_indexed": indexed_count,
            "files_failed": failed_count,
            "total_files": len(files)
        }

    async def _index_documentation(self, files: List[Path], force_refresh: bool) -> Dict[str, Any]:
        """Index documentation files"""
        indexed_count = 0
        
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                await self.mcp_client.store_context(
                    content=content,
                    context_type="documentation",
                    metadata={
                        "file_path": str(file.relative_to(self.repo_root)),
                        "file_type": file.suffix,
                        "file_size": len(content)
                    }
                )
                
                indexed_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to index documentation {file}: {e}")
        
        return {"docs_indexed": indexed_count}

    def _should_ignore_file(self, file: Path) -> bool:
        """Check if file should be ignored during indexing"""
        ignore_patterns = [
            '.git', '.svn', '.hg',
            '__pycache__', '.pyc', 
            'node_modules', '.npm',
            '.vscode', '.idea',
            'target', 'build', 'dist',
            '.env', '.DS_Store'
        ]
        
        file_str = str(file)
        return any(pattern in file_str for pattern in ignore_patterns)

    def _is_test_file(self, file: Path) -> bool:
        """Check if file is a test file"""
        test_indicators = ['test_', '_test', '.test.', '/test/', '/tests/']
        file_str = str(file).lower()
        return any(indicator in file_str for indicator in test_indicators)

    def _extract_code_structures(self, content: str, file_extension: str) -> List[Dict[str, Any]]:
        """Extract functions, classes, and other structures from code"""
        structures = []
        
        if file_extension == '.py':
            structures.extend(self._extract_python_structures(content))
        elif file_extension in ['.js', '.ts', '.tsx']:
            structures.extend(self._extract_javascript_structures(content))
        
        return structures

    def _extract_python_structures(self, content: str) -> List[Dict[str, Any]]:
        """Extract Python functions and classes"""
        structures = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Function definitions
            if re.match(r'^\s*def\s+(\w+)\s*\(', line):
                match = re.search(r'def\s+(\w+)\s*\(', line)
                if match:
                    structures.append({
                        "type": "function",
                        "name": match.group(1),
                        "code": line.strip(),
                        "line": i + 1
                    })
            
            # Class definitions
            elif re.match(r'^\s*class\s+(\w+)', line):
                match = re.search(r'class\s+(\w+)', line)
                if match:
                    structures.append({
                        "type": "class", 
                        "name": match.group(1),
                        "code": line.strip(),
                        "line": i + 1
                    })
        
        return structures

    def _extract_javascript_structures(self, content: str) -> List[Dict[str, Any]]:
        """Extract JavaScript/TypeScript functions and classes"""
        structures = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Function declarations
            if re.search(r'function\s+(\w+)\s*\(', line):
                match = re.search(r'function\s+(\w+)\s*\(', line)
                if match:
                    structures.append({
                        "type": "function",
                        "name": match.group(1),
                        "code": line.strip(),
                        "line": i + 1
                    })
            
            # Class declarations
            elif re.search(r'class\s+(\w+)', line):
                match = re.search(r'class\s+(\w+)', line)
                if match:
                    structures.append({
                        "type": "class",
                        "name": match.group(1), 
                        "code": line.strip(),
                        "line": i + 1
                    })
        
        return structures

    def _extract_dependencies(self, content: str, file_extension: str) -> List[str]:
        """Extract dependencies from file content"""
        dependencies = []
        
        if file_extension == '.py':
            # Python imports
            import_patterns = [
                r'import\s+([\w.]+)',
                r'from\s+([\w.]+)\s+import'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                dependencies.extend(matches)
        
        elif file_extension in ['.js', '.ts', '.tsx']:
            # JavaScript/TypeScript imports
            import_patterns = [
                r'import.*from\s+[\'"]([^\'"]+)[\'"]',
                r'require\([\'"]([^\'"]+)[\'"]\)'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                dependencies.extend(matches)
        
        return list(set(dependencies))  # Remove duplicates

    async def _find_dependents(self, file_path: str) -> List[str]:
        """Find files that depend on the given file"""
        # This would require searching through the indexed codebase
        # For now, return empty list as placeholder
        return []

    async def _find_related_files(self, file_path: str, content: str) -> List[str]:
        """Find files related to the given file based on content similarity"""
        # Extract key terms from the file
        key_terms = self._extract_key_terms(content)
        
        if not key_terms:
            return []
        
        # Search for files with similar terms
        query = " ".join(key_terms[:5])
        results = await self.mcp_client.query_context(
            query=query,
            top_k=10,
            threshold=0.6,
            context_types=["code_index"]
        )
        
        related_files = []
        for result in results:
            related_file = result.get("metadata", {}).get("file_path")
            if related_file and related_file != file_path:
                related_files.append(related_file)
        
        return related_files

    def _extract_key_terms(self, content: str) -> List[str]:
        """Extract key terms from content for similarity analysis"""
        # Simple term extraction - could be enhanced with NLP
        terms = re.findall(r'\b[A-Z][a-z]+|[a-z]+[A-Z][a-z]*\b', content)
        
        # Filter common programming terms
        common_terms = {
            'return', 'function', 'class', 'import', 'export', 
            'const', 'let', 'var', 'def', 'if', 'else', 'for', 'while'
        }
        
        key_terms = [term for term in set(terms) if term.lower() not in common_terms]
        
        return key_terms[:20]  # Return top 20 terms

    def _build_semantic_query(self, query: str, language: Optional[str], file_patterns: Optional[List[str]]) -> str:
        """Build enhanced semantic query"""
        query_parts = [query]
        
        if language:
            query_parts.append(f"language:{language}")
        
        if file_patterns:
            for pattern in file_patterns:
                query_parts.append(f"file:{pattern}")
        
        return " ".join(query_parts)

    async def _enhance_search_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance search result with additional context"""
        # Add file context, related functions, etc.
        enhanced = dict(result)
        
        file_path = result.get("metadata", {}).get("file_path")
        if file_path:
            # Add file statistics
            enhanced["file_context"] = {
                "language": self.language_extensions.get(Path(file_path).suffix, "other"),
                "relative_path": file_path
            }
        
        return enhanced

    def _extract_code_features(self, code: str, language: Optional[str]) -> List[str]:
        """Extract features from code for similarity analysis"""
        features = []
        
        # Extract function/method names
        if language == "python":
            features.extend(re.findall(r'def\s+(\w+)', code))
            features.extend(re.findall(r'class\s+(\w+)', code))
        elif language in ["javascript", "typescript"]:
            features.extend(re.findall(r'function\s+(\w+)', code))
            features.extend(re.findall(r'class\s+(\w+)', code))
        
        # Extract variable patterns
        features.extend(re.findall(r'\b[a-z_][a-z0-9_]*\b', code.lower()))
        
        return list(set(features))

    def _calculate_code_similarity(self, code1: str, code2: str) -> float:
        """Calculate similarity between two code snippets"""
        # Simple Jaccard similarity based on tokens
        tokens1 = set(re.findall(r'\w+', code1.lower()))
        tokens2 = set(re.findall(r'\w+', code2.lower()))
        
        if not tokens1 and not tokens2:
            return 1.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0

    async def _analyze_code_patterns(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze common code patterns across the repository"""
        patterns = {
            "common_imports": {},
            "design_patterns": [],
            "function_patterns": {},
            "naming_conventions": {}
        }
        
        # This would be a more comprehensive analysis
        # For now, return basic structure
        return patterns

    def _analyze_architectural_patterns(self, context_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze architectural patterns from context"""
        return {
            "mvc_patterns": 0,
            "singleton_patterns": 0, 
            "observer_patterns": 0,
            "factory_patterns": 0
        }

    async def _calculate_complexity_metrics(self) -> Dict[str, Any]:
        """Calculate code complexity metrics"""
        return {
            "cyclomatic_complexity": 0,
            "coupling_metrics": {},
            "cohesion_metrics": {}
        }

    async def _identify_hotspots(self) -> List[Dict[str, Any]]:
        """Identify code hotspots (files that change frequently)"""
        return []

    async def _generate_recommendations(self) -> List[str]:
        """Generate architectural recommendations"""
        return [
            "Consider refactoring large files",
            "Improve test coverage",
            "Review dependency structure"
        ]