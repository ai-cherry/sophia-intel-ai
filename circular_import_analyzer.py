import ast
from collections import defaultdict
from pathlib import Path
class CircularImportAnalyzer:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.imports = defaultdict(set)
        self.files = {}
    def analyze_file(self, file_path):
        """Analyze a Python file for imports"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
            return imports
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return set()
    def build_import_graph(self):
        """Build import dependency graph"""
        python_files = list(self.root_dir.rglob("*.py"))
        for file_path in python_files:
            if any(
                skip in str(file_path)
                for skip in [".git", ".venv", "migration_backup", "__pycache__"]
            ):
                continue
            relative_path = file_path.relative_to(self.root_dir)
            module_name = str(relative_path).replace("/", ".").replace(".py", "")
            imports = self.analyze_file(file_path)
            self.files[module_name] = str(file_path)
            for imp in imports:
                if imp.startswith("."):
                    continue  # Skip relative imports for now
                self.imports[module_name].add(imp)
    def find_cycles(self):
        """Find circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        cycles = []
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            if node in visited:
                return
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in self.imports.get(node, []):
                if neighbor in self.files:  # Only check internal modules
                    dfs(neighbor, path.copy())
            rec_stack.remove(node)
        for module in self.files:
            if module not in visited:
                dfs(module, [])
        return cycles
# Analyze the current directory
analyzer = CircularImportAnalyzer(".")
analyzer.build_import_graph()
cycles = analyzer.find_cycles()
print("=== CIRCULAR IMPORT ANALYSIS ===")
if cycles:
    print(f"Found {len(cycles)} circular dependencies:")
    for i, cycle in enumerate(cycles, 1):
        print(f"\nCycle {i}: {' -> '.join(cycle)}")
else:
    print("No circular dependencies found!")
# Check specific memory router files
memory_files = [f for f in analyzer.files if "memory" in f and "router" in f]
print("\n=== MEMORY ROUTER FILES ===")
for file in memory_files:
    print(f"File: {file}")
    imports = analyzer.imports.get(file, set())
    memory_imports = [imp for imp in imports if "memory" in imp.lower()]
    if memory_imports:
        print(f"  Memory-related imports: {memory_imports}")
