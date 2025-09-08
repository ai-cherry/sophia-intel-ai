"""
Code Intelligence System
========================
Deep understanding of repository structure and code
"""

import ast
import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a code file"""

    path: str
    language: str
    size: int
    lines: int
    imports: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    last_modified: Optional[datetime] = None
    complexity: Optional[int] = None


@dataclass
class ModuleInfo:
    """Information about a code module/package"""

    name: str
    path: str
    type: str  # package, module, library
    files: list[FileInfo] = field(default_factory=list)
    submodules: list[str] = field(default_factory=list)
    dependencies: set[str] = field(default_factory=set)
    exports: list[str] = field(default_factory=list)


class CodeIntelligence:
    """
    Deep understanding of repository structure and code
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.file_cache: dict[str, FileInfo] = {}
        self.module_cache: dict[str, ModuleInfo] = {}
        self.dependency_graph: dict[str, set[str]] = {}
        self.reverse_dependencies: dict[str, set[str]] = {}
        self.tech_stack: dict[str, Any] = {}
        self.patterns: dict[str, list[dict]] = {}

    async def analyze_repository(self) -> dict[str, Any]:
        """Build comprehensive repository understanding"""
        logger.info(f"Analyzing repository: {self.repo_path}")

        analysis = {
            "structure": await self._analyze_structure(),
            "dependencies": await self._analyze_dependencies(),
            "patterns": await self._detect_patterns(),
            "quality_metrics": await self._calculate_metrics(),
            "hot_spots": await self._identify_hot_spots(),
            "tech_debt": await self._assess_tech_debt(),
            "tech_stack": await self._detect_tech_stack(),
        }

        logger.info("Repository analysis complete")
        return analysis

    async def _analyze_structure(self) -> dict[str, Any]:
        """Analyze repository structure"""
        structure = {
            "root": str(self.repo_path),
            "modules": {},
            "directories": {},
            "file_count": 0,
            "total_lines": 0,
        }

        # Walk through repository
        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden and cache directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

            rel_path = Path(root).relative_to(self.repo_path)

            # Process Python modules
            if "__init__.py" in files:
                module_name = str(rel_path).replace("/", ".")
                module_info = await self._analyze_module(Path(root))
                self.module_cache[module_name] = module_info
                structure["modules"][module_name] = {
                    "path": str(rel_path),
                    "files": len(module_info.files),
                    "exports": len(module_info.exports),
                }

            # Process all code files
            for file in files:
                if self._is_code_file(file):
                    file_path = Path(root) / file
                    file_info = await self._analyze_file(file_path)
                    if file_info:
                        self.file_cache[str(file_path)] = file_info
                        structure["file_count"] += 1
                        structure["total_lines"] += file_info.lines

        return structure

    async def _analyze_file(self, file_path: Path) -> Optional[FileInfo]:
        """Analyze a single code file"""
        try:
            # Get file stats
            stats = file_path.stat()

            # Read file content
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.splitlines()

            # Detect language
            language = self._detect_language(file_path)

            file_info = FileInfo(
                path=str(file_path),
                language=language,
                size=stats.st_size,
                lines=len(lines),
                last_modified=datetime.fromtimestamp(stats.st_mtime),
            )

            # Language-specific analysis
            if language == "python":
                await self._analyze_python_file(file_info, content)
            elif language in ["javascript", "typescript"]:
                await self._analyze_javascript_file(file_info, content)

            return file_info

        except Exception as e:
            logger.debug(f"Error analyzing file {file_path}: {e}")
            return None

    async def _analyze_python_file(self, file_info: FileInfo, content: str):
        """Analyze Python file using AST"""
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Extract imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        file_info.imports.append(alias.name)
                        file_info.dependencies.append(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        file_info.imports.append(node.module)
                        file_info.dependencies.append(node.module.split(".")[0])

                # Extract classes
                elif isinstance(node, ast.ClassDef):
                    file_info.classes.append(node.name)
                    file_info.exports.append(node.name)

                # Extract functions
                elif isinstance(node, ast.FunctionDef):
                    file_info.functions.append(node.name)
                    if not node.name.startswith("_"):
                        file_info.exports.append(node.name)

            # Calculate complexity (simplified McCabe complexity)
            file_info.complexity = sum(
                1
                for node in ast.walk(tree)
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler))
            )

        except SyntaxError:
            logger.debug(f"Syntax error in {file_info.path}")

    async def _analyze_javascript_file(self, file_info: FileInfo, content: str):
        """Analyze JavaScript/TypeScript file using regex"""
        # Extract imports
        import_pattern = (
            r'import\s+(?:{[^}]+}|\*\s+as\s+\w+|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        )
        for match in re.finditer(import_pattern, content):
            module = match.group(1)
            file_info.imports.append(module)
            if not module.startswith("."):
                file_info.dependencies.append(module)

        # Extract exports
        export_pattern = (
            r"export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)"
        )
        for match in re.finditer(export_pattern, content):
            file_info.exports.append(match.group(1))

        # Extract classes
        class_pattern = r"class\s+(\w+)"
        for match in re.finditer(class_pattern, content):
            file_info.classes.append(match.group(1))

        # Extract functions
        func_pattern = r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=])\s*=>)"
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1) or match.group(2)
            if func_name:
                file_info.functions.append(func_name)

    async def _analyze_module(self, module_path: Path) -> ModuleInfo:
        """Analyze a Python module/package"""
        module_name = module_path.name
        module_info = ModuleInfo(
            name=module_name,
            path=str(module_path),
            type="package" if (module_path / "__init__.py").exists() else "module",
        )

        # Analyze all Python files in module
        for file_path in module_path.glob("*.py"):
            file_info = await self._analyze_file(file_path)
            if file_info:
                module_info.files.append(file_info)
                module_info.dependencies.update(file_info.dependencies)
                module_info.exports.extend(file_info.exports)

        # Find submodules
        for subdir in module_path.iterdir():
            if subdir.is_dir() and (subdir / "__init__.py").exists():
                module_info.submodules.append(subdir.name)

        return module_info

    async def _analyze_dependencies(self) -> dict[str, Any]:
        """Analyze project dependencies"""
        dependencies = {"internal": {}, "external": {}, "circular": [], "unused": []}

        # Build dependency graph
        for file_path, file_info in self.file_cache.items():
            if file_path not in self.dependency_graph:
                self.dependency_graph[file_path] = set()

            for dep in file_info.dependencies:
                # Check if dependency is internal or external
                dep_path = self._resolve_import(dep, Path(file_path).parent)
                if dep_path and dep_path in self.file_cache:
                    # Internal dependency
                    self.dependency_graph[file_path].add(dep_path)

                    # Build reverse dependencies
                    if dep_path not in self.reverse_dependencies:
                        self.reverse_dependencies[dep_path] = set()
                    self.reverse_dependencies[dep_path].add(file_path)
                else:
                    # External dependency
                    if dep not in dependencies["external"]:
                        dependencies["external"][dep] = []
                    dependencies["external"][dep].append(file_path)

        # Detect circular dependencies
        dependencies["circular"] = self._detect_circular_dependencies()

        # Find unused files
        for file_path in self.file_cache:
            if file_path not in self.reverse_dependencies and not file_path.endswith(
                "__main__.py"
            ):
                dependencies["unused"].append(file_path)

        return dependencies

    def _resolve_import(self, import_name: str, current_dir: Path) -> Optional[str]:
        """Resolve import to file path"""
        # Try relative import
        possible_paths = [
            current_dir / f"{import_name}.py",
            current_dir / import_name / "__init__.py",
            self.repo_path / f"{import_name.replace('.', '/')}.py",
            self.repo_path / import_name.replace(".", "/") / "__init__.py",
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        return None

    def _detect_circular_dependencies(self) -> list[list[str]]:
        """Detect circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: list[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.dependency_graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            rec_stack.remove(node)
            return False

        for node in self.dependency_graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    async def _detect_patterns(self) -> dict[str, list[dict]]:
        """Detect code patterns and conventions"""
        patterns = {
            "naming_conventions": [],
            "design_patterns": [],
            "anti_patterns": [],
            "code_smells": [],
        }

        # Analyze naming conventions
        class_names = []
        function_names = []
        for file_info in self.file_cache.values():
            class_names.extend(file_info.classes)
            function_names.extend(file_info.functions)

        # Detect naming patterns
        if class_names and all(name[0].isupper() for name in class_names if name):
            patterns["naming_conventions"].append(
                {"type": "class_naming", "pattern": "PascalCase", "confidence": 0.95}
            )

        if function_names:
            snake_case = sum(1 for name in function_names if "_" in name)
            camel_case = sum(
                1
                for name in function_names
                if name and name[0].islower() and any(c.isupper() for c in name)
            )

            if snake_case > camel_case:
                patterns["naming_conventions"].append(
                    {
                        "type": "function_naming",
                        "pattern": "snake_case",
                        "confidence": snake_case / len(function_names),
                    }
                )

        # Detect common design patterns
        for file_info in self.file_cache.values():
            # Singleton pattern
            if any(
                "instance" in func.lower() or "singleton" in func.lower()
                for func in file_info.functions
            ):
                patterns["design_patterns"].append(
                    {"type": "singleton", "file": file_info.path, "confidence": 0.7}
                )

            # Factory pattern
            if any(
                "factory" in cls.lower() or "create" in func.lower()
                for cls in file_info.classes
                for func in file_info.functions
            ):
                patterns["design_patterns"].append(
                    {"type": "factory", "file": file_info.path, "confidence": 0.6}
                )

        self.patterns = patterns
        return patterns

    async def _calculate_metrics(self) -> dict[str, Any]:
        """Calculate code quality metrics"""
        metrics = {
            "total_files": len(self.file_cache),
            "total_lines": sum(f.lines for f in self.file_cache.values()),
            "average_file_size": 0,
            "average_complexity": 0,
            "languages": {},
            "largest_files": [],
            "most_complex": [],
            "most_dependencies": [],
        }

        if self.file_cache:
            # Average metrics
            metrics["average_file_size"] = (
                metrics["total_lines"] / metrics["total_files"]
            )

            complexities = [
                f.complexity for f in self.file_cache.values() if f.complexity
            ]
            if complexities:
                metrics["average_complexity"] = sum(complexities) / len(complexities)

            # Language distribution
            for file_info in self.file_cache.values():
                lang = file_info.language
                if lang not in metrics["languages"]:
                    metrics["languages"][lang] = 0
                metrics["languages"][lang] += 1

            # Find outliers
            sorted_by_size = sorted(
                self.file_cache.values(), key=lambda f: f.lines, reverse=True
            )
            metrics["largest_files"] = [
                {"path": f.path, "lines": f.lines} for f in sorted_by_size[:5]
            ]

            sorted_by_complexity = sorted(
                [f for f in self.file_cache.values() if f.complexity],
                key=lambda f: f.complexity,
                reverse=True,
            )
            metrics["most_complex"] = [
                {"path": f.path, "complexity": f.complexity}
                for f in sorted_by_complexity[:5]
            ]

            sorted_by_deps = sorted(
                self.dependency_graph.items(), key=lambda x: len(x[1]), reverse=True
            )
            metrics["most_dependencies"] = [
                {"path": path, "count": len(deps)} for path, deps in sorted_by_deps[:5]
            ]

        return metrics

    async def _identify_hot_spots(self) -> list[dict]:
        """Identify frequently changed files using git history"""
        hot_spots = []

        try:
            # Get git log for file changes
            result = await asyncio.create_subprocess_exec(
                "git",
                "log",
                "--pretty=format:",
                "--name-only",
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await result.communicate()

            # Count file changes
            file_changes = {}
            for line in stdout.decode("utf-8").splitlines():
                if line:
                    file_changes[line] = file_changes.get(line, 0) + 1

            # Sort by change frequency
            sorted_changes = sorted(
                file_changes.items(), key=lambda x: x[1], reverse=True
            )

            # Get top hot spots
            for file_path, change_count in sorted_changes[:10]:
                full_path = self.repo_path / file_path
                if full_path.exists() and str(full_path) in self.file_cache:
                    file_info = self.file_cache[str(full_path)]
                    hot_spots.append(
                        {
                            "path": file_path,
                            "changes": change_count,
                            "lines": file_info.lines,
                            "complexity": file_info.complexity,
                            "risk_score": change_count
                            * (file_info.complexity or 1)
                            / 10,
                        }
                    )

        except Exception as e:
            logger.debug(f"Error identifying hot spots: {e}")

        return hot_spots

    async def _assess_tech_debt(self) -> dict[str, Any]:
        """Assess technical debt indicators"""
        tech_debt = {"total_score": 0, "indicators": [], "recommendations": []}

        # Check for code smells
        for file_path, file_info in self.file_cache.items():
            # Long files
            if file_info.lines > 500:
                tech_debt["indicators"].append(
                    {
                        "type": "long_file",
                        "file": file_path,
                        "severity": "medium",
                        "lines": file_info.lines,
                    }
                )
                tech_debt["total_score"] += 5

            # High complexity
            if file_info.complexity and file_info.complexity > 10:
                tech_debt["indicators"].append(
                    {
                        "type": "high_complexity",
                        "file": file_path,
                        "severity": "high",
                        "complexity": file_info.complexity,
                    }
                )
                tech_debt["total_score"] += 10

            # Too many dependencies
            if len(file_info.dependencies) > 15:
                tech_debt["indicators"].append(
                    {
                        "type": "too_many_dependencies",
                        "file": file_path,
                        "severity": "medium",
                        "count": len(file_info.dependencies),
                    }
                )
                tech_debt["total_score"] += 7

        # Check for circular dependencies
        circular_deps = self._detect_circular_dependencies()
        if circular_deps:
            for cycle in circular_deps:
                tech_debt["indicators"].append(
                    {"type": "circular_dependency", "files": cycle, "severity": "high"}
                )
                tech_debt["total_score"] += 15

        # Generate recommendations
        if tech_debt["total_score"] > 50:
            tech_debt["recommendations"].append("Consider major refactoring")
        if any(ind["type"] == "long_file" for ind in tech_debt["indicators"]):
            tech_debt["recommendations"].append(
                "Break down large files into smaller modules"
            )
        if circular_deps:
            tech_debt["recommendations"].append("Resolve circular dependencies")

        return tech_debt

    async def _detect_tech_stack(self) -> dict[str, Any]:
        """Auto-detect technology stack from project files"""
        tech_stack = {
            "languages": {},
            "frameworks": [],
            "tools": [],
            "package_managers": [],
        }

        # Check for package manager files
        package_files = {
            "requirements.txt": ("Python", "pip"),
            "Pipfile": ("Python", "pipenv"),
            "poetry.lock": ("Python", "poetry"),
            "package.json": ("JavaScript/TypeScript", "npm/yarn"),
            "Cargo.toml": ("Rust", "cargo"),
            "go.mod": ("Go", "go modules"),
            "pom.xml": ("Java", "maven"),
            "build.gradle": ("Java", "gradle"),
            "Gemfile": ("Ruby", "bundler"),
            "composer.json": ("PHP", "composer"),
        }

        for file, (lang, pm) in package_files.items():
            if (self.repo_path / file).exists():
                tech_stack["languages"][lang] = True
                tech_stack["package_managers"].append(pm)

                # Analyze package file for frameworks
                if file == "package.json":
                    await self._detect_js_frameworks(tech_stack)
                elif file in ["requirements.txt", "Pipfile", "poetry.lock"]:
                    await self._detect_python_frameworks(tech_stack)

        # Check for config files
        config_files = {
            "docker-compose.yml": "Docker",
            "Dockerfile": "Docker",
            ".github/workflows": "GitHub Actions",
            ".gitlab-ci.yml": "GitLab CI",
            "Jenkinsfile": "Jenkins",
            ".travis.yml": "Travis CI",
            "terraform": "Terraform",
            "ansible": "Ansible",
        }

        for file, tool in config_files.items():
            if (self.repo_path / file).exists():
                tech_stack["tools"].append(tool)

        self.tech_stack = tech_stack
        return tech_stack

    async def _detect_js_frameworks(self, tech_stack: dict):
        """Detect JavaScript frameworks from package.json"""
        try:
            with open(self.repo_path / "package.json") as f:
                package_data = json.load(f)

            deps = {
                **package_data.get("dependencies", {}),
                **package_data.get("devDependencies", {}),
            }

            frameworks = {
                "react": "React",
                "vue": "Vue.js",
                "angular": "Angular",
                "express": "Express.js",
                "fastify": "Fastify",
                "next": "Next.js",
                "nuxt": "Nuxt.js",
                "svelte": "Svelte",
                "nest": "NestJS",
            }

            for key, framework in frameworks.items():
                if any(key in dep.lower() for dep in deps):
                    tech_stack["frameworks"].append(framework)

        except Exception as e:
            logger.debug(f"Error detecting JS frameworks: {e}")

    async def _detect_python_frameworks(self, tech_stack: dict):
        """Detect Python frameworks from requirements"""
        try:
            # Try to read requirements file
            req_files = ["requirements.txt", "Pipfile", "pyproject.toml"]
            content = ""

            for req_file in req_files:
                file_path = self.repo_path / req_file
                if file_path.exists():
                    with open(file_path) as f:
                        content += f.read().lower()

            frameworks = {
                "django": "Django",
                "flask": "Flask",
                "fastapi": "FastAPI",
                "tornado": "Tornado",
                "pyramid": "Pyramid",
                "aiohttp": "aiohttp",
                "streamlit": "Streamlit",
                "dash": "Dash",
            }

            for key, framework in frameworks.items():
                if key in content:
                    tech_stack["frameworks"].append(framework)

        except Exception as e:
            logger.debug(f"Error detecting Python frameworks: {e}")

    def _is_code_file(self, filename: str) -> bool:
        """Check if file is a code file"""
        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".rb",
            ".go",
            ".rs",
            ".php",
            ".swift",
            ".kt",
            ".scala",
            ".r",
            ".m",
            ".mm",
            ".vue",
            ".svelte",
        }
        return Path(filename).suffix.lower() in code_extensions

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext_to_lang = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".r": "r",
            ".m": "objc",
            ".mm": "objcpp",
            ".vue": "vue",
            ".svelte": "svelte",
        }
        return ext_to_lang.get(file_path.suffix.lower(), "unknown")

    async def get_file_context(self, file_path: str) -> dict[str, Any]:
        """Get deep context for a specific file"""
        if file_path not in self.file_cache:
            # Analyze file if not in cache
            file_info = await self._analyze_file(Path(file_path))
            if file_info:
                self.file_cache[file_path] = file_info
            else:
                return {}

        file_info = self.file_cache[file_path]

        context = {
            "file_info": {
                "path": file_info.path,
                "language": file_info.language,
                "size": file_info.size,
                "lines": file_info.lines,
                "complexity": file_info.complexity,
            },
            "imports": file_info.imports,
            "exports": file_info.exports,
            "dependencies": list(self.dependency_graph.get(file_path, [])),
            "dependents": list(self.reverse_dependencies.get(file_path, [])),
            "related_files": await self._find_related_files(file_path),
            "recent_changes": await self._get_recent_changes(file_path),
        }

        return context

    async def _find_related_files(self, file_path: str) -> list[str]:
        """Find files related to the given file"""
        related = set()

        # Add direct dependencies and dependents
        related.update(self.dependency_graph.get(file_path, []))
        related.update(self.reverse_dependencies.get(file_path, []))

        # Add test files
        base_name = Path(file_path).stem
        test_patterns = [
            f"test_{base_name}.py",
            f"{base_name}_test.py",
            f"{base_name}.test.js",
            f"{base_name}.spec.js",
        ]

        for pattern in test_patterns:
            for test_file in self.repo_path.rglob(pattern):
                related.add(str(test_file))

        return list(related)[:10]  # Limit to 10 most related

    async def _get_recent_changes(self, file_path: str) -> list[dict]:
        """Get recent git changes for a file"""
        changes = []

        try:
            rel_path = Path(file_path).relative_to(self.repo_path)

            result = await asyncio.create_subprocess_exec(
                "git",
                "log",
                "-5",
                "--pretty=format:%H|%an|%ad|%s",
                str(rel_path),
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await result.communicate()

            for line in stdout.decode("utf-8").splitlines():
                if line:
                    parts = line.split("|", 3)
                    if len(parts) == 4:
                        changes.append(
                            {
                                "commit": parts[0][:8],
                                "author": parts[1],
                                "date": parts[2],
                                "message": parts[3],
                            }
                        )

        except Exception as e:
            logger.debug(f"Error getting git changes: {e}")

        return changes
