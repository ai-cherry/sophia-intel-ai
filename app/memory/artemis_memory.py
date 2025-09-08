#!/usr/bin/env python3
"""
Artemis Code Intelligence Memory Service
Handles code-specific context and retrieval
Port: 8768
"""

import ast
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.memory.base_memory import BaseMemoryService


class ArtemisMemoryService(BaseMemoryService):
    """
    Memory service for code intelligence domain
    Handles code repositories, documentation, tests, and technical content
    """

    def __init__(self):
        super().__init__(domain="artemis", port=8768)
        self.collection_name = "code_intelligence"

        # Code-specific patterns for enhanced search
        self.code_patterns = {
            "functions": ["def ", "function ", "async def ", "=>"],
            "classes": ["class ", "interface ", "struct ", "type "],
            "imports": ["import ", "from ", "require(", "using "],
            "tests": ["test_", "describe(", "it(", "assert", "expect"],
        }

        # Programming language detection
        self.language_extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "golang",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".rb": "ruby",
            ".php": "php",
        }

        # Add code-specific indexing endpoint
        @self.app.post("/index-code")
        async def index_code(document: Dict[str, Any]):
            try:
                required = ["code", "filepath"]
                if not all(k in document for k in required):
                    return {"success": False, "error": "Missing code or filepath"}
                ok = await self.index(document)
                return {"success": ok, "document_id": document.get("id")}
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def search(
        self, query: str, limit: int, filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Search code intelligence context
        Optimized for code snippets and technical documentation
        """
        # Check cache
        cache_key = self._get_cache_key(query)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached[:limit]

        results = []

        # Try Weaviate vector search for semantic code search
        if self.weaviate_client:
            try:
                # Build where filter
                where_filter = None
                if filters:
                    where_filter = self._build_code_filter(filters)

                # Use higher alpha for code (more semantic)
                weaviate_query = (
                    self.weaviate_client.query.get(
                        self.collection_name,
                        ["code", "filepath", "language", "description", "metadata"],
                    )
                    .with_hybrid(query=query, alpha=0.7)  # More semantic for code
                    .with_limit(limit * 2)
                )

                if where_filter:
                    weaviate_query = weaviate_query.with_where(where_filter)

                weaviate_results = weaviate_query.do()

                if self.collection_name in weaviate_results.get("data", {}).get("Get", {}):
                    results = weaviate_results["data"]["Get"][self.collection_name]
            except Exception as e:
                print(f"Weaviate search error: {e}")

        # Fallback to Redis pattern matching
        if not results and self.redis_available:
            # Expand query with code patterns
            search_patterns = self._expand_code_query(query)

            for pattern in search_patterns:
                redis_pattern = f"{self.domain}:code:*{pattern.lower()}*"
                for key in self.redis_client.scan_iter(match=redis_pattern, count=100):
                    doc = self.redis_client.get(key)
                    if doc:
                        doc_data = json.loads(doc)
                        # Apply filters
                        if self._apply_code_filters(doc_data, filters):
                            results.append(doc_data)
                            if len(results) >= limit * 2:
                                break

                if len(results) >= limit * 2:
                    break

        # Rank results by code relevance
        results = self._rank_code_results(results, query)

        # File-tier fallback if still no results
        if not results and getattr(self, "persistence_dir", None):
            try:
                docs_dir = self.persistence_dir / "docs"
                if docs_dir.exists():
                    q = query.lower()
                    for fp in docs_dir.glob("*.json"):
                        with open(fp) as f:
                            doc = json.load(f)
                        code_text = str(doc.get("code", doc.get("content", ""))).lower()
                        if q in code_text and self._apply_code_filters(doc, filters):
                            results.append(doc)
                            if len(results) >= limit:
                                break
            except Exception as e:
                print(f"File-tier search error: {e}")

        # Cache results
        if results:
            self._set_cache(cache_key, results, ttl=3600)  # 1 hour cache

        return results[:limit]

    async def index(self, document: Dict[str, Any]) -> bool:
        """
        Index code document with metadata extraction
        """
        try:
            # Extract and enrich code metadata
            if "code" in document or "content" in document:
                document = self._extract_code_metadata(document)

            # Auto-detect language if not provided
            if "language" not in document and "filepath" in document:
                document["language"] = self._detect_language(document["filepath"])

            # Generate document ID
            doc_id = document.get("id", f"artemis:{datetime.now().timestamp()}")
            document["id"] = doc_id
            document["domain"] = self.domain
            document["indexed_at"] = datetime.now().isoformat()

            # Store in Redis with language-specific key
            if self.redis_available:
                # Main document
                self.redis_client.setex(
                    f"{self.domain}:code:{doc_id}",
                    86400 * 30,  # 30 day TTL for code
                    json.dumps(document),
                )

                # Index by language for filtering
                if "language" in document:
                    self.redis_client.sadd(f"{self.domain}:lang:{document['language']}", doc_id)

                # Index by file type
                if "filepath" in document:
                    ext = Path(document["filepath"]).suffix
                    if ext:
                        self.redis_client.sadd(f"{self.domain}:ext:{ext}", doc_id)
            else:
                self.memory_cache[f"{self.domain}:code:{doc_id}"] = document

            # Persist to file-tier if enabled
            if getattr(self, "persistence_dir", None):
                try:
                    docs_dir = self.persistence_dir / "docs"
                    file_path = docs_dir / f"{doc_id}.json"
                    with open(file_path, "w") as f:
                        json.dump(document, f)
                except Exception as e:
                    print(f"File-tier persist error: {e}")

            # Index in Weaviate for vector search
            if self.weaviate_client:
                try:
                    # Prepare document for Weaviate
                    weaviate_doc = document.copy()
                    # Convert complex metadata to string for Weaviate
                    if "metadata" in weaviate_doc:
                        weaviate_doc["metadata"] = json.dumps(weaviate_doc["metadata"])

                    self.weaviate_client.data_object.create(weaviate_doc, self.collection_name)
                except Exception as e:
                    print(f"Weaviate indexing error: {e}")

            return True

        except Exception as e:
            print(f"Indexing error: {e}")
            return False

    async def enrich_with_context(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add code-specific context to results
        Includes language info, complexity metrics, and related files
        """
        for result in results:
            code = result.get("code", result.get("content", ""))

            # Add language context
            language = result.get("language", "unknown")
            result["language_context"] = {
                "language": language,
                "paradigm": self._get_language_paradigm(language),
                "syntax_family": self._get_syntax_family(language),
            }

            # Add complexity metrics
            if code:
                result["complexity"] = self._assess_code_complexity(code)

            # Add file relationship context
            if "filepath" in result:
                result["related_files"] = self._get_related_files(result["filepath"])

            # Add code pattern detection
            result["patterns"] = self._detect_code_patterns(code)

            # Add test coverage hint
            result["has_tests"] = self._check_test_coverage(result)

        return results


if __name__ == "__main__":
    svc = ArtemisMemoryService()
    svc.run()

    def _apply_code_filters(self, doc: Dict[str, Any], filters: Optional[Dict]) -> bool:
        if not filters:
            return True
        try:
            for k, v in filters.items():
                if str(doc.get("metadata", {}).get(k)) != str(v):
                    return False
            return True
        except Exception:
            return True

    def _extract_code_metadata(self, document: Dict) -> Dict:
        """Extract metadata from code content"""
        code = document.get("code", document.get("content", ""))

        if not code:
            return document

        metadata = {
            "lines": len(code.splitlines()),
            "characters": len(code),
            "has_classes": any(pattern in code for pattern in self.code_patterns["classes"]),
            "has_functions": any(pattern in code for pattern in self.code_patterns["functions"]),
            "has_tests": any(pattern in code for pattern in self.code_patterns["tests"]),
            "imports": [],
            "functions": [],
            "classes": [],
        }

        # Try to parse Python code for detailed metadata
        if document.get("language") == "python" or ".py" in document.get("filepath", ""):
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            metadata["imports"].append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            metadata["imports"].append(node.module)
                    elif isinstance(node, ast.FunctionDef):
                        metadata["functions"].append(node.name)
                    elif isinstance(node, ast.ClassDef):
                        metadata["classes"].append(node.name)
            except:
                pass  # Parsing failed, use basic metadata

        # Merge with existing metadata
        if "metadata" in document:
            document["metadata"].update(metadata)
        else:
            document["metadata"] = metadata

        return document

    def _detect_language(self, filepath: str) -> str:
        """Detect programming language from filepath"""
        path = Path(filepath)
        ext = path.suffix.lower()
        return self.language_extensions.get(ext, "unknown")

    def _expand_code_query(self, query: str) -> List[str]:
        """Expand query with code-specific terms"""
        terms = [query]
        query_lower = query.lower()

        # Add common code variations
        if "function" in query_lower:
            terms.extend(["def", "func", "method"])
        if "class" in query_lower:
            terms.extend(["class", "struct", "interface"])
        if "test" in query_lower:
            terms.extend(["test_", "spec", "assert", "expect"])
        if "import" in query_lower:
            terms.extend(["import", "require", "include", "using"])

        return list(set(terms))

    def _rank_code_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Rank results based on code relevance"""
        query_lower = query.lower()

        for result in results:
            score = 0
            code = str(result.get("code", result.get("content", ""))).lower()
            filepath = str(result.get("filepath", "")).lower()

            # Exact match in code
            if query_lower in code:
                score += 10

            # Match in filepath
            if query_lower in filepath:
                score += 8

            # Match in function/class names
            metadata = result.get("metadata", {})
            for func in metadata.get("functions", []):
                if query_lower in func.lower():
                    score += 7
            for cls in metadata.get("classes", []):
                if query_lower in cls.lower():
                    score += 7

            # Language match bonus
            if "language" in result:
                if result["language"] in query_lower:
                    score += 3

            # Recent code bonus
            if "indexed_at" in result:
                try:
                    doc_time = datetime.fromisoformat(result["indexed_at"])
                    age_days = (datetime.now() - doc_time).days
                    if age_days < 1:
                        score += 5
                    elif age_days < 7:
                        score += 2
                except:
                    pass

            # Test code bonus (tests are often good examples)
            if metadata.get("has_tests"):
                score += 2

            result["_score"] = score

        return sorted(results, key=lambda x: x.get("_score", 0), reverse=True)

    def _apply_code_filters(self, document: Dict, filters: Optional[Dict]) -> bool:
        """Apply code-specific filters"""
        if not filters:
            return True

        # Language filter
        if "language" in filters:
            if document.get("language") != filters["language"]:
                return False

        # File extension filter
        if "extension" in filters:
            if "filepath" in document:
                ext = Path(document["filepath"]).suffix
                if ext != filters["extension"]:
                    return False

        # Has tests filter
        if "has_tests" in filters:
            metadata = document.get("metadata", {})
            if metadata.get("has_tests", False) != filters["has_tests"]:
                return False

        return True

    def _build_code_filter(self, filters: Dict) -> Dict:
        """Build Weaviate where filter for code"""
        where = {"operator": "And", "operands": []}

        if "language" in filters:
            where["operands"].append(
                {"path": ["language"], "operator": "Equal", "valueString": filters["language"]}
            )

        return where if where["operands"] else None

    def _assess_code_complexity(self, code: str) -> Dict:
        """Assess code complexity metrics"""
        lines = code.splitlines()

        # Simple complexity metrics
        complexity = {
            "lines": len(lines),
            "avg_line_length": sum(len(line) for line in lines) / max(len(lines), 1),
            "nesting_depth": max(len(line) - len(line.lstrip()) for line in lines) // 4,
            "complexity_level": "low",
        }

        # Determine complexity level
        if complexity["lines"] > 100 or complexity["nesting_depth"] > 4:
            complexity["complexity_level"] = "high"
        elif complexity["lines"] > 50 or complexity["nesting_depth"] > 2:
            complexity["complexity_level"] = "medium"

        return complexity

    def _get_language_paradigm(self, language: str) -> str:
        """Get programming paradigm for language"""
        paradigms = {
            "python": "multi-paradigm",
            "javascript": "multi-paradigm",
            "java": "object-oriented",
            "golang": "procedural",
            "rust": "systems",
            "haskell": "functional",
            "c": "procedural",
            "cpp": "multi-paradigm",
        }
        return paradigms.get(language, "unknown")

    def _get_syntax_family(self, language: str) -> str:
        """Get syntax family for language"""
        families = {
            "python": "python-like",
            "javascript": "c-like",
            "java": "c-like",
            "golang": "c-like",
            "rust": "c-like",
            "ruby": "ruby-like",
            "php": "c-like",
            "c": "c-like",
            "cpp": "c-like",
        }
        return families.get(language, "unknown")

    def _get_related_files(self, filepath: str) -> Dict:
        """Get related file paths"""
        path = Path(filepath)
        stem = path.stem

        return {
            "test_file": str(path.parent / f"test_{stem}.py"),
            "spec_file": str(path.parent / f"{stem}_spec.py"),
            "doc_file": str(path.parent / f"{stem}.md"),
            "config_file": str(path.parent / f"{stem}.config.json"),
        }

    def _detect_code_patterns(self, code: str) -> List[str]:
        """Detect common code patterns"""
        patterns = []
        code_lower = code.lower()

        # Design patterns
        if "singleton" in code_lower or "@singleton" in code:
            patterns.append("singleton")
        if "factory" in code_lower and ("create" in code_lower or "build" in code_lower):
            patterns.append("factory")
        if "observer" in code_lower or "subscribe" in code_lower:
            patterns.append("observer")

        # Code patterns
        if "async def" in code or "await " in code:
            patterns.append("async")
        if "try:" in code or "except:" in code:
            patterns.append("error-handling")
        if "@cache" in code or "lru_cache" in code:
            patterns.append("caching")

        return patterns

    def _check_test_coverage(self, result: Dict) -> bool:
        """Check if code has associated tests"""
        # Check metadata
        if result.get("metadata", {}).get("has_tests"):
            return True

        # Check filepath
        filepath = result.get("filepath", "")
        if "test" in filepath.lower() or "spec" in filepath.lower():
            return True

        # Check code content
        code = result.get("code", result.get("content", ""))
        return any(pattern in code for pattern in self.code_patterns["tests"])


if __name__ == "__main__":
    service = ArtemisMemoryService()
    service.run()
